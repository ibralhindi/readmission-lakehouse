## Phase 5: FHIR optional-cardinality fields in contracts

reasonCode (Encounter, 0..*) was modeled as a required list, quarantining 37%
of encounters (all routine visits with null reasonCode). Fixed to optional.
TODO: audit all contracts for 0..* fields modeled as required lists — they're
latent quarantine bugs that only surface when a dataset nulls them.
