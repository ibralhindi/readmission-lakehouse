{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH bronze_condition AS (
    SELECT *
    FROM {{ source('silver_validated', 'condition_valid') }}
),

flattened AS (
    SELECT
        id AS condition_id,
        {{ extract_fhir_id('subject.reference') }} AS patient_id,
        {{ extract_fhir_id('encounter.reference') }} AS encounter_id,
        code.coding[0].code AS snomed_code,
        code.coding[0].display AS snomed_display,
        clinicalStatus.coding[0].code AS clinical_status,
        verificationStatus.coding[0].code AS verification_status,
        category[0].coding[0].code AS category_code,
        {{ parse_fhir_timestamp('onsetDateTime') }} AS onset_time,
        {{ parse_fhir_timestamp('abatementDateTime') }} AS abatement_time,
        {{ parse_fhir_timestamp('recordedDate') }} AS recorded_time,
        _load_ts AS _bronze_load_ts,
        _source_file AS _bronze_source_file,
        _row_hash AS _bronze_row_hash,
        _ingestion_run_id AS _bronze_ingestion_run_id
    FROM bronze_condition
)

SELECT * FROM flattened
