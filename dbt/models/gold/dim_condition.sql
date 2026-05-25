{{ config(materialized='table', file_format='delta') }}

-- Condition reference dimension. One row per distinct SNOMED code seen in the
-- data. NOT SCD2 — a code's meaning doesn't change over time, so no history.
-- Built by deduplicating silver.condition.
--
-- occurrence_count is a useful "how common is this condition" metric — handy
-- for spotting the top comorbidities driving readmission risk.

SELECT
    {{ dbt_utils.generate_surrogate_key(['snomed_code']) }} AS condition_key,
    snomed_code,
    MAX(snomed_display) AS snomed_display,
    COUNT(*) AS occurrence_count
FROM {{ ref('condition') }}
WHERE snomed_code IS NOT NULL
GROUP BY snomed_code
