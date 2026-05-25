{{ config(materialized='table', file_format='delta') }}

-- Date dimension. One row per calendar day. The date_key is a "smart key" —
-- an integer YYYYMMDD — which is the classic Kimball pattern: human-readable,
-- sortable, and joins faster than a date type. Facts store date_key FKs.
--
-- Range covers all plausible encounter/birth dates in the Synthea cohort.
-- Synthea patients span ~1900s births to present; we use 1900–2030 to be safe.

WITH date_spine AS (
    -- dbt_utils.date_spine generates a contiguous series of dates.
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('1900-01-01' as date)",
        end_date="cast('2030-01-01' as date)"
    ) }}
)

SELECT
    cast(date_format(date_day, 'yyyyMMdd') as int) AS date_key,
    date_day AS full_date,
    year(date_day) AS year,
    quarter(date_day) AS quarter,
    month(date_day) AS month,
    date_format(date_day, 'MMMM') AS month_name,
    day(date_day) AS day_of_month,
    dayofweek(date_day) AS day_of_week,
    date_format(date_day, 'EEEE') AS day_name,
    dayofweek(date_day) IN (1, 7) AS is_weekend
FROM date_spine
