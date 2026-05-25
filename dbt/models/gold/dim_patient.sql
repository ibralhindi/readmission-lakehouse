{{ config(materialized='table', file_format='delta') }}

-- SCD2 patient dimension. Sources the snapshot so every demographic version is
-- preserved with its validity window. Facts join to the version that was valid
-- at the event date (as-of join, implemented in fact_encounter).
--
-- SURROGATE KEY: patient_key = hash(patient_id + valid_from). Why not just use
-- patient_id?
--   - One patient_id maps to MULTIPLE rows here (one per SCD2 version), so
--     patient_id alone isn't unique — can't be a PK.
--   - Surrogate keys decouple the warehouse from source natural keys: if the
--     source system changes its ID scheme, facts keep working.
--   - Integer/hash keys join faster than long string natural keys.
-- We include valid_from in the hash so each version gets a distinct key.

SELECT
    {{ dbt_utils.generate_surrogate_key(['patient_id', 'dbt_valid_from']) }} AS patient_key,
    patient_id,
    gender,
    birth_date,
    race_code,
    race_display,
    ethnicity_code,
    ethnicity_display,
    marital_status_code,
    address_city,
    address_state,
    address_postal_code,
    dbt_valid_from AS valid_from,
    dbt_valid_to AS valid_to,
    (dbt_valid_to IS NULL) AS is_current,
    dbt_scd_id AS _snapshot_scd_id
FROM {{ ref('patient_snapshot') }}
