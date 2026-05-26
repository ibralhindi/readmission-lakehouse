{{ config(
    materialized='incremental',
    unique_key='observation_id',
    incremental_strategy='merge',
    file_format='delta'
) }}

-- Silver model: rl_dev.silver.observation
--
-- READS FROM BRONZE, NOT silver_validated — Observation has no Pydantic
-- contract yet (see docs/decisions.md, contract-coverage gap). When a contract
-- is added, switch the source to silver_validated.observation_valid.
--
-- Observation uses a polymorphic value[x]: each row has exactly ONE of
-- valueQuantity / valueCodeableConcept / valueString (or a component[] array
-- for multi-part obs like blood pressure). We extract every variant as a
-- nullable column. Vitals and labs are the readmission-relevant ones.

WITH bronze_observation AS (
    SELECT *
    FROM {{ source('bronze', 'observation') }}
),

flattened AS (
    SELECT
        id AS observation_id,
        {{ extract_fhir_id('subject.reference') }} AS patient_id,
        {{ extract_fhir_id('encounter.reference') }} AS encounter_id,
        status,
        category[0].coding[0].code AS category_code,        -- vital-signs / laboratory / survey
        code.coding[0].code AS loinc_code,                  -- LOINC
        code.coding[0].display AS loinc_display,
        {{ parse_fhir_timestamp('effectiveDateTime') }} AS effective_time,
        valueQuantity.value AS value_number,
        valueQuantity.unit AS value_unit,
        valueCodeableConcept.coding[0].code AS value_code,
        valueCodeableConcept.coding[0].display AS value_display,
        valueString AS value_text,
        _load_ts AS _bronze_load_ts,
        _source_file AS _bronze_source_file,
        _row_hash AS _bronze_row_hash,
        _ingestion_run_id AS _bronze_ingestion_run_id
    FROM bronze_observation
)

SELECT * FROM flattened
{% if is_incremental() %}
  -- Only process observations newer than what's already loaded.
  WHERE effective_time > (SELECT MAX(effective_time) FROM {{ this }})
{% endif %}
