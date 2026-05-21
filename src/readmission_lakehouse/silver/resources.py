"""Catalogue of bronze→silver-valid validations.

Maps each bronze table to its Pydantic contract. The 6 entities with Phase 2
contracts get full validation; Observation and MedicationRequest are deferred
(see docs/decisions.md for the contract-coverage gap).
"""

from dataclasses import dataclass

from pydantic import BaseModel

from readmission_lakehouse.contracts.fhir import (
    ConditionContract,
    EncounterContract,
    OrganizationContract,
    PatientContract,
    PractitionerContract,
    ProcedureContract,
)


@dataclass(frozen=True)
class SilverValidation:
    """Configuration for one bronze→silver-valid validation."""

    bronze_table: str
    valid_table: str
    quarantine_table: str
    contract: type[BaseModel]
    name: str


SILVER_VALIDATIONS: list[SilverValidation] = [
    SilverValidation(
        bronze_table="rl_dev.bronze.patient",
        valid_table="rl_dev.silver.patient_valid",
        quarantine_table="rl_dev.silver.patient_quarantine",
        contract=PatientContract,
        name="Patient",
    ),
    SilverValidation(
        bronze_table="rl_dev.bronze.encounter",
        valid_table="rl_dev.silver.encounter_valid",
        quarantine_table="rl_dev.silver.encounter_quarantine",
        contract=EncounterContract,
        name="Encounter",
    ),
    SilverValidation(
        bronze_table="rl_dev.bronze.condition",
        valid_table="rl_dev.silver.condition_valid",
        quarantine_table="rl_dev.silver.condition_quarantine",
        contract=ConditionContract,
        name="Condition",
    ),
    SilverValidation(
        bronze_table="rl_dev.bronze.procedure",
        valid_table="rl_dev.silver.procedure_valid",
        quarantine_table="rl_dev.silver.procedure_quarantine",
        contract=ProcedureContract,
        name="Procedure",
    ),
    SilverValidation(
        bronze_table="rl_dev.bronze.organization",
        valid_table="rl_dev.silver.organization_valid",
        quarantine_table="rl_dev.silver.organization_quarantine",
        contract=OrganizationContract,
        name="Organization",
    ),
    SilverValidation(
        bronze_table="rl_dev.bronze.practitioner",
        valid_table="rl_dev.silver.practitioner_valid",
        quarantine_table="rl_dev.silver.practitioner_quarantine",
        contract=PractitionerContract,
        name="Practitioner",
    ),
]

# TODO(phase-5-followup): write Pydantic contracts for Observation and
# MedicationRequest, then add entries here. Their silver dbt models currently
# read directly from bronze (see dbt/models/silver/observation.sql,
# medication_request.sql) — bypassing the validation pattern.
