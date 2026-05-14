"""Pydantic contracts for the subset of FHIR resources used in the project."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FHIR_MODEL_CONFIG = ConfigDict(extra="ignore", frozen=True, populate_by_name=True)


class FHIRReference(BaseModel):
    """FHIR reference wrapper with a convenience accessor for the referenced id."""

    model_config = FHIR_MODEL_CONFIG

    reference: str

    @property
    def target_id(self) -> str:
        """Return the raw referenced resource id without FHIR-specific prefixes."""

        raw_reference = self.reference.removeprefix("urn:uuid:")
        if "/" in raw_reference and not raw_reference.startswith("http"):
            return raw_reference.rsplit("/", maxsplit=1)[-1]
        return raw_reference


class Coding(BaseModel):
    """FHIR Coding value object."""

    model_config = FHIR_MODEL_CONFIG

    system: str | None = None
    code: str | None = None
    display: str | None = None


class CodeableConcept(BaseModel):
    """FHIR CodeableConcept value object."""

    model_config = FHIR_MODEL_CONFIG

    coding: list[Coding] = Field(default_factory=list)
    text: str | None = None


class PatientContract(BaseModel):
    """Canonical FHIR Patient contract template for the remaining resource models."""

    model_config = FHIR_MODEL_CONFIG

    id: str
    gender: Literal["male", "female", "other", "unknown"]
    birth_date: date = Field(alias="birthDate")
    deceased_date_time: datetime | None = Field(default=None, alias="deceasedDateTime")
    address: list[dict[str, object]] = Field(default_factory=list)
    marital_status: CodeableConcept | None = Field(default=None, alias="maritalStatus")
    extension: list[dict[str, object]] = Field(default_factory=list)


class EncounterContract(BaseModel):
    """Typed subset of a FHIR Encounter resource."""

    model_config = FHIR_MODEL_CONFIG

    id: str
    status: str
    # FHIR: Encounter.class -> Coding
    class_: Coding = Field(alias="class")
    type: list[CodeableConcept] = Field(default_factory=list)
    subject: FHIRReference
    period: dict[str, datetime | None]
    # FHIR: Encounter.reasonCode -> list[CodeableConcept]
    reason_code: list[CodeableConcept] = Field(default_factory=list, alias="reasonCode")
    hospitalization: dict[str, object] | None = None
    location: list[dict[str, object]] = Field(default_factory=list)
    # FHIR: Encounter.serviceProvider -> FHIRReference | None
    service_provider: FHIRReference | None = Field(default=None, alias="serviceProvider")
    participant: list[dict[str, object]] = Field(default_factory=list)


class ConditionContract(BaseModel):
    """Typed subset of a FHIR Condition resource."""

    model_config = FHIR_MODEL_CONFIG

    id: str
    # FHIR: Condition.clinicalStatus -> CodeableConcept | None
    clinical_status: CodeableConcept | None = Field(default=None, alias="clinicalStatus")
    # FHIR: Condition.verificationStatus -> CodeableConcept | None
    verification_status: CodeableConcept | None = Field(default=None, alias="verificationStatus")
    category: list[CodeableConcept] = Field(default_factory=list)
    code: CodeableConcept
    subject: FHIRReference
    encounter: FHIRReference | None = None
    # FHIR: Condition.onsetDateTime -> datetime | None
    onset_date_time: datetime | None = Field(default=None, alias="onsetDateTime")
    # FHIR: Condition.recordedDate -> datetime | None
    recorded_date: datetime | None = Field(default=None, alias="recordedDate")


class ProcedureContract(BaseModel):
    """Typed subset of a FHIR Procedure resource."""

    model_config = FHIR_MODEL_CONFIG

    id: str
    status: str
    code: CodeableConcept
    subject: FHIRReference
    encounter: FHIRReference | None = None
    # FHIR: Procedure.performedDateTime -> datetime | None
    performed_date_time: datetime | None = Field(default=None, alias="performedDateTime")
    # FHIR: Procedure.performedPeriod -> dict[str, datetime | None] | None
    performed_period: dict[str, datetime | None] | None = Field(
        default=None,
        alias="performedPeriod",
    )


class OrganizationContract(BaseModel):
    """Typed subset of a FHIR Organization resource."""

    model_config = FHIR_MODEL_CONFIG

    id: str
    name: str
    type: list[CodeableConcept] = Field(default_factory=list)
    address: list[dict[str, object]] = Field(default_factory=list)
    telecom: list[dict[str, object]] = Field(default_factory=list)


class PractitionerContract(BaseModel):
    """Typed subset of a FHIR Practitioner resource."""

    model_config = FHIR_MODEL_CONFIG

    id: str
    name: list[dict[str, object]]
    gender: str | None = None
    address: list[dict[str, object]] = Field(default_factory=list)
    telecom: list[dict[str, object]] = Field(default_factory=list)


RESOURCE_REGISTRY: dict[str, type[BaseModel]] = {
    "Patient": PatientContract,
    "Encounter": EncounterContract,
    "Condition": ConditionContract,
    "Procedure": ProcedureContract,
    "Organization": OrganizationContract,
    "Practitioner": PractitionerContract,
}
