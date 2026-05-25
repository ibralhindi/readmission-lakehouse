{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH bronze_organization AS (
    SELECT *
    FROM {{ source('silver_validated', 'organization_valid') }}
),

flattened AS (
    SELECT id AS organization_id,
    name,
    type[0].coding[0].code AS type_code,
    type[0].coding[0].display AS type_display,
    address[0].line[0] AS address_line,
    address[0].city AS address_city,
    address[0].state AS address_state,
    address[0].postalCode AS address_postal_code,
    telecom[0].value AS phone,
    _load_ts AS _bronze_load_ts,
    _source_file AS _bronze_source_file,
    _row_hash AS _bronze_row_hash,
    _ingestion_run_id AS _bronze_ingestion_run_id
    FROM bronze_organization
)

SELECT * FROM flattened
