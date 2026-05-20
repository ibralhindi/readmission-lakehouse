"""Catalogue of FHIR resources bronzed in the readmission-lakehouse project.

This module is the single source of truth for "which resources do we ingest and
where do they live." Adding or removing a resource = editing this list.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BronzeResource:
    """Configuration for one FHIR resource type's bronze ingestion."""

    name: str  # FHIR resource type, e.g. "Patient"
    source_glob: str  # filename glob within raw/synthea/, e.g. "Patient.ndjson.gz"
    table_name: str  # bronze table name (snake_case), e.g. "patient"


# Order roughly by importance: facts before dimensions, common before rare.
# Glob patterns with .* handle the timestamped filenames from Synthea's
# hospital/practitioner exporters.
BRONZE_RESOURCES: list[BronzeResource] = [
    BronzeResource("Patient", "Patient.ndjson.gz", "patient"),
    BronzeResource("Encounter", "Encounter.ndjson.gz", "encounter"),
    BronzeResource("Condition", "Condition.ndjson.gz", "condition"),
    BronzeResource("Procedure", "Procedure.ndjson.gz", "procedure"),
    BronzeResource("Observation", "Observation.ndjson.gz", "observation"),
    BronzeResource("MedicationRequest", "MedicationRequest.ndjson.gz", "medication_request"),
    BronzeResource("Immunization", "Immunization.ndjson.gz", "immunization"),
    BronzeResource("Claim", "Claim.ndjson.gz", "claim"),
    BronzeResource("AllergyIntolerance", "AllergyIntolerance.ndjson.gz", "allergy_intolerance"),
    BronzeResource("CarePlan", "CarePlan.ndjson.gz", "care_plan"),
    BronzeResource("CareTeam", "CareTeam.ndjson.gz", "care_team"),
    BronzeResource("DocumentReference", "DocumentReference.ndjson.gz", "document_reference"),
    BronzeResource("Organization", "Organization.*.ndjson.gz", "organization"),
    BronzeResource("Practitioner", "Practitioner.*.ndjson.gz", "practitioner"),
]
