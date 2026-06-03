{% snapshot patient_snapshot %}

{{
    config(
        target_schema='silver',
        unique_key='patient_id',
        strategy='check',
        check_cols=[
            'address_city',
            'address_state',
            'address_postal_code',
            'marital_status_code',
        ],
        file_format='delta',
        invalidate_hard_deletes=True,
    )
}}

-- SCD2 history of patient demographics. Reads from the silver patient model;
-- gold.dim_patient builds on this snapshot so the dimension
-- carries full validity-window history.
--
-- check_cols: only the demographic attributes that can plausibly change. We
-- deliberately DON'T include birth_date or gender (those shouldn't change;
-- if they do, that's a data-quality issue, not a slowly-changing attribute).

SELECT * FROM {{ ref('patient') }}

{% endsnapshot %}
