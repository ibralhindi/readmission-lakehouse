## Phase 5: FHIR optional-cardinality fields in contracts

reasonCode (Encounter, 0..*) was modeled as a required list, quarantining 37%
of encounters (all routine visits with null reasonCode). Fixed to optional.
TODO: audit all contracts for 0..* fields modeled as required lists — they're
latent quarantine bugs that only surface when a dataset nulls them.

## Phase 6: Provider dimension deferred on fact_encounter

fact_encounter resolves patient (as-of SCD2) and organization FKs but NOT
provider. Reason: the encounter references the attending practitioner by NPI
(`Practitioner?identifier=http://hl7.org/fhir/sid/us-npi|<npi>`), whereas
dim_provider is keyed on the practitioner resource UUID. Joining requires
extracting NPI from silver.practitioner.identifier AND from the encounter's
participant[] array (the latter not yet extracted), then keying on NPI.
Deferred — provider is dimensional enrichment, not core to patient-centric
readmission analytics. Contrast: organization joins fine because Synthea's
org identifier value equals the org resource UUID, so a UUID join coincidentally
works. Lesson: FHIR identifier-references resolve per identifier-system; a join
that works on one reference type can silently fail on another.
