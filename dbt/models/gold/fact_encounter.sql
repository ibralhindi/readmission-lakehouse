{{ config(materialized='table', file_format='delta') }}

-- Central fact: one row per encounter. Foreign keys to all dimensions plus
-- the encounter's measures. Grain = one encounter.
--
-- KEY CONCEPT — the as-of join: each encounter joins to the dim_patient version
-- that was VALID AT ADMISSION TIME (start_time falls within [valid_from, valid_to)),
-- not the current version. This is the entire payoff of SCD2: a fact always sees
-- the dimension as it was when the event happened.
--
-- Organization uses a current-version join instead — orgs are stable (no changes
-- in our data) and we don't need point-in-time org attributes. This is a realistic
-- mixed pattern: as-of for dims where history matters, current for stable refs.
--
-- Provider (attending practitioner) is DEFERRED: the encounter references
-- practitioners by NPI identifier (Practitioner?identifier=us-npi|xxx), not by
-- resource id, so joining to dim_provider needs NPI extraction on both sides.

WITH encounter AS (
    SELECT * FROM {{ ref('encounter') }}
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['e.encounter_id']) }} AS encounter_key,
    e.encounter_id,
    p.patient_key,
    o.organization_key,
    cast(date_format(e.start_time, 'yyyyMMdd') as int) AS admission_date_key,
    cast(date_format(e.end_time, 'yyyyMMdd') as int) AS discharge_date_key,
    e.encounter_class_code,
    e.encounter_class_display,
    e.status,
    e.encounter_type_code,
    e.discharge_disposition_code,
    e.length_of_stay_hours
FROM encounter e

-- As-of join to the patient version valid at admission time.
LEFT JOIN {{ ref('dim_patient') }} p
    ON e.patient_id = p.patient_id
    AND e.start_time >= p.valid_from
    AND (e.start_time < p.valid_to OR p.valid_to IS NULL)

-- Current-version join to organization.
LEFT JOIN {{ ref('dim_organization') }} o
    ON e.service_provider_id = o.organization_id
    AND o.is_current = true
