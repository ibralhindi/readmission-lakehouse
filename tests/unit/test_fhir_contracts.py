# mypy: disable-error-code="untyped-decorator"
"""Contract validation tests for the FHIR subset models.

These tests check that the project's typed FHIR boundary accepts realistic
minimal payloads and still preserves the alias behavior the pipeline relies on
when validating raw Synthea JSON.
"""

from __future__ import annotations

from typing import Any, cast

import pytest
from pydantic import ValidationError

from readmission_lakehouse.contracts.fhir import (
    RESOURCE_REGISTRY,
    EncounterContract,
    FHIRReference,
    PatientContract,
)

# Pytest's decorators are dynamically typed, so this file opts out of that specific mypy warning
# rather than weakening type checking for the rest of the test suite.


@pytest.fixture
def patient_payload() -> dict[str, Any]:
    return {
        "id": "patient-001",
        "gender": "female",
        "birthDate": "1984-07-05",
        "deceasedDateTime": None,
        "address": [{"city": "Boston"}],
        "maritalStatus": {"text": "Married"},
        "extension": [{"url": "http://example.org/ext"}],
    }


@pytest.fixture
def encounter_payload() -> dict[str, Any]:
    return {
        "id": "encounter-001",
        "status": "finished",
        "class": {"code": "AMB", "display": "ambulatory"},
        "type": [{"text": "Outpatient encounter"}],
        "subject": {"reference": "Patient/patient-001"},
        "period": {"start": "2024-01-15T09:30:00Z", "end": "2024-01-15T10:30:00Z"},
        "reasonCode": [{"text": "Follow-up"}],
        "hospitalization": {"dischargeDisposition": {"text": "Home"}},
        "location": [{"location": {"display": "Clinic 1"}}],
        "serviceProvider": {"reference": "Organization/org-001"},
        "participant": [{"individual": {"reference": "Practitioner/prac-001"}}],
    }


@pytest.fixture
def condition_payload() -> dict[str, Any]:
    return {
        "id": "condition-001",
        "clinicalStatus": {"text": "active"},
        "verificationStatus": {"text": "confirmed"},
        "category": [{"text": "encounter-diagnosis"}],
        "code": {"coding": [{"code": "44054006", "display": "Diabetes mellitus type 2"}]},
        "subject": {"reference": "Patient/patient-001"},
        "encounter": {"reference": "Encounter/encounter-001"},
        "onsetDateTime": "2023-11-01T00:00:00Z",
        "recordedDate": "2023-11-02T00:00:00Z",
    }


@pytest.fixture
def procedure_payload() -> dict[str, Any]:
    return {
        "id": "procedure-001",
        "status": "completed",
        "code": {"text": "Appendectomy"},
        "subject": {"reference": "Patient/patient-001"},
        "encounter": {"reference": "Encounter/encounter-001"},
        "performedDateTime": "2024-02-01T08:00:00Z",
        "performedPeriod": {"start": "2024-02-01T08:00:00Z", "end": "2024-02-01T09:00:00Z"},
    }


@pytest.fixture
def organization_payload() -> dict[str, Any]:
    return {
        "id": "org-001",
        "name": "General Hospital",
        "type": [{"text": "Hospital"}],
        "address": [{"city": "Boston"}],
        "telecom": [{"system": "phone", "value": "555-0100"}],
    }


@pytest.fixture
def practitioner_payload() -> dict[str, Any]:
    return {
        "id": "prac-001",
        "name": [{"family": "Jones", "given": ["Ava"]}],
        "gender": "female",
        "address": [{"city": "Boston"}],
        "telecom": [{"system": "email", "value": "ava.jones@example.org"}],
    }


@pytest.mark.parametrize(
    ("resource_type", "fixture_name"),
    [
        ("Patient", "patient_payload"),
        ("Encounter", "encounter_payload"),
        ("Condition", "condition_payload"),
        ("Procedure", "procedure_payload"),
        ("Organization", "organization_payload"),
        ("Practitioner", "practitioner_payload"),
    ],
)
def test_registry_validates_minimal_resource_payloads(
    request: pytest.FixtureRequest,
    resource_type: str,
    fixture_name: str,
) -> None:
    # ``request.getfixturevalue`` is a pytest idiom for parameterizing over fixture names when the
    # fixture itself cannot be referenced directly in the parametrized list.
    payload = request.getfixturevalue(fixture_name)
    contract_type = RESOURCE_REGISTRY[resource_type]

    validated = contract_type.model_validate(payload)
    # The registry returns different model classes, so ``cast`` sidesteps a static typing blind
    # spot and lets the test assert against the shared ``id`` field.
    validated_id = cast(Any, validated).id

    assert validated_id == payload["id"]


def test_invalid_patient_gender_raises_validation_error(
    patient_payload: dict[str, Any],
) -> None:
    patient_payload["gender"] = "invalid"

    with pytest.raises(ValidationError):
        PatientContract.model_validate(patient_payload)


def test_fhir_reference_target_id_strips_common_prefixes() -> None:
    patient_reference = FHIRReference(reference="Patient/patient-001")
    urn_reference = FHIRReference(reference="urn:uuid:patient-002")

    assert patient_reference.target_id == "patient-001"
    assert urn_reference.target_id == "patient-002"


def test_encounter_contract_populates_alias_backed_class_field(
    encounter_payload: dict[str, Any],
) -> None:
    encounter = EncounterContract.model_validate(encounter_payload)

    assert encounter.class_.code == "AMB"
    assert encounter.subject.target_id == "patient-001"
