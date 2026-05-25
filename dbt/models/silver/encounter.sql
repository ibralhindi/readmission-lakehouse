{{ config(
    materialized='table',
    file_format='delta'
) }}

-- Silver model: rl_dev.silver.encounter
--
-- One row per encounter. Central fact for readmission analytics — every gold
-- table joins back here. Key fields for the readmission window calculation:
--   - period.start / period.end (admission and discharge timestamps)
--   - class.code (inpatient vs ambulatory — readmissions are defined for IMP)
--   - subject.reference (patient_id for joining demographics + comorbidities)
--
-- The hospitalization sub-resource (discharge_disposition, etc.) is only
-- populated on ~0.1% of Synthea encounters per the Phase 2 profiler.
-- We extract it anyway — when present, it's gold for risk modelling.

WITH bronze_encounter AS (
    SELECT *
    FROM {{ source('silver_validated', 'encounter_valid') }}
),

typed AS (
    SELECT
        id AS encounter_id,
        status,
        class.code AS encounter_class_code,
        CASE class.code
            WHEN 'IMP'  THEN 'inpatient encounter'
            WHEN 'AMB'  THEN 'ambulatory'
            WHEN 'EMER' THEN 'emergency'
            WHEN 'HH'   THEN 'home health'
            WHEN 'VR'   THEN 'virtual'
            ELSE class.code
        END AS encounter_class_display,
        type[0].coding[0].code AS encounter_type_code,
        type[0].coding[0].display AS encounter_type_display,
        {{ extract_fhir_id('subject.reference') }} AS patient_id,
        {{ parse_fhir_timestamp('period.start') }} AS start_time,
        {{ parse_fhir_timestamp('period.end') }} AS end_time,
        {{ extract_fhir_id('serviceProvider.reference') }} AS service_provider_id,
        hospitalization.dischargeDisposition.coding[0].code AS discharge_disposition_code,
        hospitalization.dischargeDisposition.coding[0].display AS discharge_disposition_display,
        reasonCode[0].coding[0].code AS reason_code,
        reasonCode[0].coding[0].display AS reason_display,
        _load_ts AS _bronze_load_ts,
        _source_file AS _bronze_source_file,
        _row_hash AS _bronze_row_hash,
        _ingestion_run_id AS _bronze_ingestion_run_id
    FROM bronze_encounter
),

flattened AS (
    SELECT
        *,
        (unix_timestamp(end_time) - unix_timestamp(start_time)) / 3600.0 AS length_of_stay_hours
    FROM typed
)

SELECT * FROM flattened
