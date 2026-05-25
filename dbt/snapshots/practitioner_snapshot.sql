{% snapshot practitioner_snapshot %}
{{
    config(
        target_schema='silver',
        unique_key='practitioner_id',
        strategy='check',
        check_cols=['family_name', 'given_name', 'address_city', 'address_state'],
        file_format='delta',
        invalidate_hard_deletes=True,
    )
}}
SELECT * FROM {{ ref('practitioner') }}
{% endsnapshot %}
