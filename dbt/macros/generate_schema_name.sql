{#
  Override of dbt's built-in generate_schema_name macro.

  Default behaviour concatenates target.schema + custom_schema_name, producing
  "silver_silver" when both are set. We want the custom schema name used as-is
  so models in models/silver/ land in rl_dev.silver, models/gold/ in rl_dev.gold.

  When no +schema: is configured on a model, falls back to target.schema.

  https://docs.getdbt.com/docs/build/custom-schemas#changing-the-way-dbt-generates-a-schema-name
#}

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
