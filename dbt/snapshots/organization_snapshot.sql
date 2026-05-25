{% snapshot organization_snapshot %}
{{
    config(
        target_schema='silver',
        unique_key='organization_id',
        strategy='check',
        check_cols=['name', 'address_city', 'address_state', 'address_postal_code'],
        file_format='delta',
        invalidate_hard_deletes=True,
    )
}}
SELECT * FROM {{ ref('organization') }}
{% endsnapshot %}
