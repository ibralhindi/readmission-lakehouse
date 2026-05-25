{#
  Extract the bare resource ID from a FHIR reference. Handles both formats
  Synthea emits:
    Direct:  "Patient/abc-123"                    -> abc-123
    Logical: "Organization?identifier=sys|abc-123" -> abc-123
    URN:     "urn:uuid:abc-123"                     -> abc-123

  Logical references put the meaningful value after the pipe; direct/URN
  references put it after a prefix. We detect the pipe and branch.
#}
{% macro extract_fhir_id(column) %}
    CASE
        WHEN {{ column }} LIKE '%|%'
            THEN split({{ column }}, '\\|')[1]
        ELSE regexp_replace({{ column }}, '^([A-Za-z]+/|urn:uuid:)', '')
    END
{% endmacro %}
