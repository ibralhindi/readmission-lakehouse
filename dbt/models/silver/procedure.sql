{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH bronze_procedure AS (
    SELECT *
    FROM {{ source('silver_validated', 'procedure_valid') }}
),

flattened AS (
    SELECT
        id AS procedure_id,
        {{ extract_fhir_id('subject.reference') }} AS patient_id,
        {{ extract_fhir_id('encounter.reference') }} AS encounter_id,
        code.coding[0].code AS snomed_code,
        code.coding[0].display AS snomed_display,
        status,
        {{ parse_fhir_timestamp('performedPeriod.start') }} AS performed_start,
        {{ parse_fhir_timestamp('performedPeriod.end') }} AS performed_end,
        reasonCode[0].coding[0].code AS reason_code,
        _load_ts AS _bronze_load_ts,
        _source_file AS _bronze_source_file,
        _row_hash AS _bronze_row_hash,
        _ingestion_run_id AS _bronze_ingestion_run_id
    FROM bronze_procedure
)

SELECT * FROM flattened
