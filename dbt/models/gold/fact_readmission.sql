{{ config(materialized='table', file_format='delta') }}

-- Readmission fact. Grain: one row per INPATIENT (IMP) index admission.
-- For each index admission, flags whether the patient had another IMP
-- admission within 30 days of discharge — the standard CMS-style 30-day
-- readmission definition.
--
-- This is the analytical centrepiece: readmission rate = AVG(was_readmitted_30d).
--
-- Simplifications vs the full CMS measure (documented, defensible):
--   - No planned-readmission exclusion (CMS excludes elective readmits).
--   - No same-day transfer merging (CMS combines transfers into one stay).
--   - No death-within-window exclusion (we have deceased_date but don't use it).
-- These are noted as future refinements; the core windowing is identical.

WITH imp_encounters AS (
    -- Inpatient admissions only — readmission is defined for inpatient care.
    SELECT
        encounter_id,
        patient_id,
        start_time AS admission_time,
        end_time   AS discharge_time
    FROM {{ ref('encounter') }}
    WHERE encounter_class_code = 'IMP'
),

with_next AS (
    SELECT
        *,
        LEAD(admission_time) OVER (PARTITION BY patient_id ORDER BY admission_time) AS next_admission_time,
        LEAD(encounter_id) OVER (PARTITION BY patient_id ORDER BY admission_time) AS next_encounter_id
    FROM imp_encounters
),

flagged AS (
    SELECT
        *,
        CAST(DATEDIFF(next_admission_time, discharge_time) AS INT) AS days_to_readmission,
        CASE WHEN
            next_admission_time IS NOT NULL AND DATEDIFF(next_admission_time, discharge_time)
            BETWEEN 0 AND 30 THEN TRUE ELSE FALSE END AS was_readmitted_30d,
        -- Same-day "readmissions" are almost always inter-facility transfers,
        -- which CMS folds into the index stay. Flag them and offer a
        -- transfer-excluded rate (the more defensible headline: ~13.6% vs 19.28%).
        CASE WHEN next_admission_time IS NOT NULL
              AND DATEDIFF(next_admission_time, discharge_time) = 0
             THEN TRUE ELSE FALSE END AS is_likely_transfer,

        CASE WHEN next_admission_time IS NOT NULL
              AND DATEDIFF(next_admission_time, discharge_time) BETWEEN 1 AND 30
             THEN TRUE ELSE FALSE END AS was_readmitted_30d_excl_transfers
    FROM with_next
)

SELECT
    -- Keys (join back to fact_encounter for the surrogate keys)
    fe.encounter_key AS readmission_key,     -- PK; grain = index admission, so 1:1 with the index encounter
    fe.encounter_key AS index_encounter_key, -- FK to fact_encounter
    fe.patient_key,                          -- FK to dim_patient
    f.encounter_id   AS index_encounter_id,  -- degenerate
    fe.admission_date_key  AS index_admission_date_key,
    fe.discharge_date_key  AS index_discharge_date_key,

    -- Readmission measures
    f.next_encounter_id,
    f.days_to_readmission,
    f.was_readmitted_30d,
    f.is_likely_transfer,
    f.was_readmitted_30d_excl_transfers
FROM flagged f
JOIN {{ ref('fact_encounter') }} fe
    ON f.encounter_id = fe.encounter_id
