{#
  Parse a FHIR dateTime string (ISO 8601 with timezone offset) to a Spark
  TIMESTAMP. Uses try_to_timestamp so malformed values become NULL rather
  than failing the whole build.

  Handles the "+10:00"-style offset via the XXX pattern token.
#}
{% macro parse_fhir_timestamp(column) %}
    try_to_timestamp({{ column }}, "yyyy-MM-dd'T'HH:mm:ssXXX")
{% endmacro %}
