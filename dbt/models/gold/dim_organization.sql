{{ config(materialized='table', file_format='delta') }}

SELECT
    {{ dbt_utils.generate_surrogate_key(['organization_id', 'dbt_valid_from']) }} AS organization_key,
    organization_id,
    name,
    type_code,
    type_display,
    address_line,
    address_city,
    address_state,
    address_postal_code,
    phone,
    dbt_valid_from AS valid_from,
    dbt_valid_to AS valid_to,
    (dbt_valid_to IS NULL) AS is_current,
    dbt_scd_id AS _snapshot_scd_id
FROM {{ ref('organization_snapshot') }}
