{{ config(
    materialized='table',
    file_format='delta'
) }}

-- Silver model: rl_dev.silver.patient
--
-- Flattens FHIR Patient resource into a tabular form. Keeps only the columns
-- we actually use downstream — the full FHIR resource lives in bronze if
-- someone needs the raw structure.
--
-- One row per patient. No SCD here (we capture demographic changes via
-- dbt snapshots in Step 5.4).

WITH bronze_patient AS (
    SELECT *
    FROM {{ source('bronze', 'patient') }}
),

flattened AS (
    SELECT
        id AS patient_id,
        gender,
        birthDate AS birth_date,
        deceasedDateTime AS deceased_date,
        maritalStatus.coding[0].code AS marital_status_code,
        filter(extension, x -> x.url LIKE '%us-core-race')[0].extension[0].valueCoding.code        AS race_code,
        filter(extension, x -> x.url LIKE '%us-core-race')[0].extension[0].valueCoding.display     AS race_display,
        filter(extension, x -> x.url LIKE '%us-core-ethnicity')[0].extension[0].valueCoding.code   AS ethnicity_code,
        filter(extension, x -> x.url LIKE '%us-core-ethnicity')[0].extension[0].valueCoding.display AS ethnicity_display,
        address[0].city AS address_city,
        address[0].state AS address_state,
        address[0].postalCode AS address_postal_code,
        address[0].country AS address_country,
        _load_ts AS _bronze_load_ts,
        _source_file AS _bronze_source_file,
        _row_hash AS _bronze_row_hash,
        _ingestion_run_id AS _bronze_ingestion_run_id
    FROM bronze_patient
)

SELECT * FROM flattened
