{{ config(
    materialized='table',
    file_format='delta'
) }}

WITH bronze_practitioner AS (
    SELECT *
    FROM {{ source('silver_validated', 'practitioner_valid') }}
),

flattened AS (
    SELECT id AS practitioner_id,
    name[0].family AS family_name,
    name[0].given[0] AS given_name,
    name[0].prefix[0] AS prefix,
    gender,
    address[0].city AS address_city,
    address[0].state AS address_state,
    filter(telecom, x -> x.system = 'email')[0].value AS email,
    _load_ts AS _bronze_load_ts,
    _source_file AS _bronze_source_file,
    _row_hash AS _bronze_row_hash,
    _ingestion_run_id AS _bronze_ingestion_run_id
    FROM bronze_practitioner
)

SELECT * FROM flattened
