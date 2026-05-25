# Project State — End of Phase 5

Last updated: 2026-05-25. Phase 5 complete. Phases 1–5 of 11 done.

## Project Context

Hospital 30-day readmission risk lakehouse on Azure. Cross-industry parallel = churn.
Owner: Ibrahim Al-Hindi (data scientist + CPA → data engineer).
Budget $500. Repo: github.com/ibralhindi/readmission-lakehouse (public).

## Tech Stack (locked)

Python 3.12 + uv + ruff + mypy. Synthea FHIR R4 NDJSON, 10k MA patients seed=42.
Azure australiaeast. Terraform 1.15 + azurerm 4.x + azuread 3.x + databricks 1.x.
Databricks Premium, DBR 17.3 LTS. PySpark 3.5 + delta-spark 3.2. dbt-databricks 1.12
(dbt-core 1.11). LangGraph (Phase 8) + OpenAI + Chroma. Power BI. Airflow 3.x (Phase 7).

## Working Agreements (unchanged)

Tier scaffolding A/B/C. End-of-phase snapshots + quizzes + decisions log.
WHY-not-WHAT comments. AI collaboration disclosed in README. See .cursor/rules/.

## Repo Structure
readmission-lakehouse/
├── databricks.yml                          # Asset Bundle root
├── resources/
│   ├── bronze_ingestion.yml                # for_each, 14 resources
│   └── silver_validation.yml               # for_each, 6 contracted entities
├── dbt/
│   ├── dbt_project.yml                      # profile: readmission_dbt, silver materialized=table
│   ├── packages.yml                         # dbt_utils
│   ├── macros/
│   │   ├── generate_schema_name.sql         # override: use +schema verbatim (no concat)
│   │   ├── parse_fhir_timestamp.sql         # try_to_timestamp w/ XXX offset token
│   │   └── extract_fhir_id.sql              # handles direct + logical reference formats
│   ├── models/silver/
│   │   ├── _sources.yml                     # bronze + silver_validated sources
│   │   ├── _silver_models.yml               # tests + docs for 8 models
│   │   ├── patient.sql  encounter.sql  condition.sql  procedure.sql
│   │   ├── organization.sql  practitioner.sql
│   │   └── observation.sql  medication_request.sql   # read from bronze (no contract)
│   └── snapshots/
│       ├── patient_snapshot.sql             # SCD2, check strategy
│       ├── organization_snapshot.sql
│       └── practitioner_snapshot.sql
├── src/readmission_lakehouse/
│   ├── bronze/{cli,ingest,resources}.py
│   ├── silver/{cli,validate,resources}.py   # Pydantic validation + quarantine
│   ├── contracts/fhir.py                    # 6 contracts; RESOURCE_REGISTRY dict
│   └── tools/{profile_synthea,sample_synthea}.py
├── tests/unit/{bronze,silver}/              # 34 dbt tests + pytest unit tests
├── docs/{data-dictionary,decisions,quiz-log,project-state}.md
└── pyproject.toml                           # scripts: rl-bronze-ingest, rl-silver-validate

External (not in repo): `~/.dbt/profiles.yml` — OAuth U2M, catalog=rl_dev, schema=silver,
http_path to rl-dev-interactive cluster.

## Live Azure Resources

### Carryover (Phases 3–4)
RG rl-rg-dev | Storage rlst3e33 (ADLS Gen2) | Key Vault rl-kv-3e33 |
DBX workspace rl-dbx-3e33 (Premium) | Access Connector rl-ac-3e33 | CI app rl-gh-actions-dev (OIDC).

### Unity Catalog
Metastore metastore_azure_australiaeast (auto, empty-root). Catalog rl_dev (ISOLATED).
Schemas bronze/silver/gold w/ per-schema managed_location. Storage credential
rl-access-connector-dev. External locations rl-{bronze,silver,gold,raw}-dev.

### Databricks compute + jobs
- Cluster rl-dev-interactive (DBR 17.3 LTS, DS3_v2, single-node) — dbt + ad-hoc.
- Job bronze-ingestion (for_each 14 resources).
- Job silver-validation (for_each 6 contracted entities).

## Data Inventory

### Bronze (rl_dev.bronze.*) — 14 tables, ~11.3M rows. FHIR struct + 4 metadata cols.

### Silver validated (rl_dev.silver.*_valid / *_quarantine)
6 contracted entities each have _valid + _quarantine. After the reasonCode contract
fix, all 6 are 100% valid (0 quarantine). The 246,890 encounters initially quarantined
were a contract bug (reasonCode modeled as required; it's 0..* in FHIR), not bad data.

### Silver conformed (rl_dev.silver.*) — 8 models, flat + typed

| Table | Rows | Source | Notes |
|---|---|---|---|
| patient | 11,423 | patient_valid | race/ethnicity via URL-filtered extension |
| encounter | 664,623 | encounter_valid | central fact; LOS computed |
| condition | 412,692 | condition_valid | SNOMED comorbidities |
| procedure | 1,848,211 | procedure_valid | SNOMED, performedPeriod |
| organization | 1,141 | organization_valid | dimension |
| practitioner | 1,141 | practitioner_valid | dimension |
| observation | 5,862,543 | **bronze** (no contract) | polymorphic value[x]; components deferred |
| medication_request | 573,225 | **bronze** (no contract) | medicationCodeableConcept (RxNorm) |

Encounter class distribution: AMB 621,188 (93%), EMER 24,467, IMP 12,689, HH 4,878, VR 1,401.
**Readmission analytics scope = ~12,689 IMP encounters.** Hospitalization sub-resource
(discharge disposition) populated on only 0.33% (2,183) of encounters.

### SCD2 snapshots (rl_dev.silver.*_snapshot)
patient_snapshot, organization_snapshot, practitioner_snapshot. check strategy.
Demonstrated: a simulated patient address change produced contiguous validity windows.
Gold dim_patient (Phase 6) will build on patient_snapshot for as-of-date demographics.

## Phase Status

- [COMPLETED] 1 Scaffolding | 2 Synthea + contracts | 3 Azure infra | 4 Bronze | 5 Silver
- [PENDING] 6 Gold (Kimball star) | 7 Airflow | 8 RAG/LangGraph | 9 Power BI | 10 CI/dbt | 11 README

## Cost Tracker

| Phase | Spend |
|---|---|
| 1–3 | <$1 |
| 4 | ~$2 |
| 5 | ~$6 (many dbt runs, 2× full validation incl. encounter reprocess, observation 5.8M build) |
| **Total** | **~$9** of $500 |

## Key Interview Talking Points (Phase 5 additions)

**Quarantine pattern (the headline story)**:
- Validation quarantined 37% of encounters; investigation showed contract bug, not data bug
- reasonCode is 0..* in FHIR; we modeled it required → 246,890 routine-visit encounters failed
- Quarantine surfaced it without crashing the pipeline or silently dropping a third of encounters
- "Validation is a feedback loop on your contracts as much as your data"
- Fix: reasonCode optional via before-validator (null → empty list); added regression test

**Schema-on-read vs Pydantic contract**:
- Spark-inferred schema = union of fields PRESENT in data, not full theoretical FHIR schema
- Synthea omits class.display entirely → Spark never created the subfield → FIELD_NOT_FOUND
- A contract can mark display optional and validate fine; doesn't materialize the column
- When flattening schema-on-read data, reference only fields the inference found, or guard

**FHIR reference formats (direct vs logical)**:
- Direct: "Patient/<id>". Logical: "Organization?identifier=<system>|<value>"
- Synthea mixes them: direct for patient, logical for org/practitioner
- Naive prefix-strip handles one, silently mangles the other
- extract_fhir_id macro detects pipe → logical (split on |) vs prefix → direct (regexp strip)

**Hybrid Pydantic + dbt architecture**:
- Pydantic (Python) for row-level validation — expressive, structured errors, reuses contracts
- dbt (SQL) for transformation — readable, testable, lineage, snapshots
- Pure-dbt teams skip Pydantic (less expressive validation); pure-PySpark teams write SQL-as-Python (hard to review)

**dbt macros for DRY**:
- parse_fhir_timestamp (try_to_timestamp + XXX offset token for +10:00-style offsets)
- extract_fhir_id (dual-format reference parsing)
- generate_schema_name override: default concatenates target+custom = "silver_silver";
  override returns custom verbatim → medallion schemas land correctly

**SCD2 via dbt snapshots**:
- check strategy (no reliable source timestamp; compare demographic cols)
- Excluded birth_date/gender from check_cols (changing = data-quality issue, not slow change)
- dbt manages dbt_valid_from/to, dbt_scd_id, dbt_updated_at; valid_to NULL = current
- Contiguous validity windows (old.valid_to == new.valid_from) = correct as-of resolution

**Timestamp timezone artifact**:
- Synthea used the generating machine's local TZ → all timestamps +10:00 (Melbourne AEST),
  not patient-local (Massachusetts -05:00). Relative differences (readmission window) preserved.

**Cost discipline**: silver validation re-run cost ~$0 extra by reusing the for_each shared
cluster; observation (5.8M) materialised in one dbt run on the same cluster.
