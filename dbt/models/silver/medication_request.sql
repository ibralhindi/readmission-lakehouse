{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH bronze_medication_request AS (
    SELECT *
    FROM {{ source('bronze', 'medication_request') }}
),

flattened AS (
    SELECT id AS medication_request_id,
    {{ extract_fhir_id('subject.reference') }} AS patient_id,
    {{ extract_fhir_id('encounter.reference') }} AS encounter_id,
    medicationCodeableConcept.coding[0].code AS rxnorm_code,
    medicationCodeableConcept.coding[0].display AS rxnorm_display,
    status,
    intent,
    {{ parse_fhir_timestamp('authoredOn') }} AS authored_time,
    {{ extract_fhir_id('requester.reference') }} AS requester_id,
    _load_ts AS _bronze_load_ts,
    _source_file AS _bronze_source_file,
    _row_hash AS _bronze_row_hash,
    _ingestion_run_id AS _bronze_ingestion_run_id
    FROM bronze_medication_request
)

SELECT * FROM flattened
