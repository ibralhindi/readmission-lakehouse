{{ config(materialized='table', file_format='delta') }}

SELECT
    {{ dbt_utils.generate_surrogate_key(['practitioner_id', 'dbt_valid_from']) }} AS provider_key,
    practitioner_id,
    family_name,
    given_name,
    prefix,
    gender,
    address_city,
    address_state,
    email,
    dbt_valid_from AS valid_from,
    dbt_valid_to AS valid_to,
    (dbt_valid_to IS NULL) AS is_current,
    dbt_scd_id AS _snapshot_scd_id
FROM {{ ref('practitioner_snapshot') }}
