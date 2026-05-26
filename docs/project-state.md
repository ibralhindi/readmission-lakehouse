# Project State — End of Phase 6

Last updated: 2026-05-25. Phase 6 complete. Phases 1–6 of 11 done.

## Project Context

Hospital 30-day readmission risk lakehouse on Azure. Cross-industry parallel = churn.
Owner: Ibrahim Al-Hindi (data scientist + CPA → data engineer). Budget $500.
Repo: github.com/ibralhindi/readmission-lakehouse (public).

## Tech Stack (locked)

Python 3.12 / uv / ruff / mypy. Synthea FHIR R4, 10k MA patients seed=42. Azure
australiaeast. Terraform 1.15 + azurerm/azuread/databricks providers. Databricks
Premium DBR 17.3 LTS. PySpark 3.5 + delta-spark 3.2. dbt-databricks 1.12 + dbt_utils.
LangGraph (Phase 8) + OpenAI + Chroma. Power BI. Airflow 3.x (Phase 7).

## Working Agreements (unchanged)

Tier scaffolding A/B/C. Snapshots + quizzes + decisions log per phase. WHY-not-WHAT
comments. AI collaboration disclosed in README.

## Repo Structure (gold additions)

dbt/
├── macros/{generate_schema_name, parse_fhir_timestamp, extract_fhir_id}.sql
├── models/
│   ├── silver/  (8 models: patient, encounter, condition, procedure,
│   │             organization, practitioner, observation, medication_request)
│   └── gold/
│       ├── _gold_models.yml
│       ├── dim_date.sql            # generated, date_spine, smart key YYYYMMDD
│       ├── dim_patient.sql         # SCD2 from snapshot, valid_from floored to 1900
│       ├── dim_provider.sql        # SCD2 from snapshot
│       ├── dim_organization.sql    # SCD2 from snapshot
│       ├── dim_condition.sql       # reference dim, distinct SNOMED (310 codes)
│       ├── fact_encounter.sql      # central fact, as-of patient join + current org join
│       └── fact_readmission.sql    # 30-day window calc (LEAD), one row per IMP admission
└── snapshots/{patient,organization,practitioner}_snapshot.sql

## Live Azure Resources

UC: metastore_azure_australiaeast (empty-root). Catalog rl_dev (ISOLATED), schemas
bronze/silver/gold. Storage cred rl-access-connector-dev, external locations
rl-{bronze,silver,gold,raw}-dev. Cluster rl-dev-interactive (DBR 17.3 LTS, DS3_v2,
single-node). Jobs: bronze-ingestion, silver-validation.

## Data Inventory

### Bronze — 14 tables, ~11.3M rows (FHIR struct + metadata)

### Silver — 8 conformed tables + 6 _valid/_quarantine pairs + 3 SCD2 snapshots

(all 100% valid after the reasonCode contract fix)

### Gold (rl_dev.gold.*) — star schema

Dimensions:

- dim_date (47,482 days, 1900–2030, smart key YYYYMMDD)
- dim_patient (SCD2; 11,425 versions / 11,423 patients; valid_from floored to 1900 for as-of)
- dim_provider (SCD2, 1,141)
- dim_organization (SCD2, 1,141)
- dim_condition (reference, 310 distinct SNOMED codes)

Facts:

- fact_encounter (664,623; FKs to patient [as-of], organization [current], date)
- fact_readmission (12,689 IMP index admissions)

### Headline analytics

**30-day readmission rate: 13.64% (transfer-excluded) / 19.28% (raw).** The raw
rate double-counts 716 same-day inter-facility transfers (CMS folds these into
the index stay). Transfer-excluded is the defensible figure — close to the
real-world ~15% benchmark. Day-level distribution is bimodal (day-0 transfer
spike + a days-28-30 Synthea module-scheduling cluster), so the synthetic rate
isn't quoted as epidemiological truth.

## Phase Status

- [COMPLETED] 1 Scaffold | 2 Contracts | 3 Infra | 4 Bronze | 5 Silver | 6 Gold
- [PENDING] 7 Airflow | 8 RAG/LangGraph | 9 Power BI | 10 CI/dbt | 11 README

## Cost Tracker


| Phase     | Spend                                                     |
| --------- | --------------------------------------------------------- |
| 1–3       | <$1                                                       |
| 4         | ~$2                                                       |
| 5         | ~$6                                                       |
| 6         | ~$4 (multiple dbt runs, full build, observation rebuilds) |
| **Total** | **~$13** of $500                                          |


## Key Interview Talking Points (Phase 6 additions)

**Kimball star schema**: facts (skinny, long, FKs + measures) surrounded by dims
(wide, short, descriptive). Surrogate keys link them, decoupling warehouse from
source IDs and enabling SCD2.

**Surrogate keys**: hash(natural_key [+ valid_from for SCD2]). One patient_id →
many patient_keys (one per version), so patient_id can't be PK. dim_condition is
the exception — natural key (snomed_code) IS unique because it's a deduplicated
reference dim, not versioned.

**SCD2 as-of join**: facts join to the dimension version valid AT EVENT TIME, not
current. Window predicate: start_time >= valid_from AND start_time < valid_to (NULL
valid_to = open). Verification = row-count conservation (fact == source, 0 dupes):
overlap → fan-out/double-count, gap → dropped rows. Floored earliest valid_from to
1900 so historical events (all predating our 2026 snapshot) resolve to the original version.

**FHIR identifier vs resource-id references**: references resolve by resource id
(Patient/uuid) or by business identifier (Type?identifier=system|value). For identifier
refs the value is namespace-specific: Synthea's org identifier = resource UUID (UUID
join works), but practitioner identifier = NPI (≠ UUID, join needs NPI on both sides).
A join that works on one reference type can silently fail on another. Provider FK deferred.

**30-day readmission window (LEAD)**: partition by patient, order by admission_time,
LEAD() to get next admission, datediff to discharge, flag 0-30 days. Last admission
per patient → NULL next → not readmitted. datediff truncates time (day granularity, correct).

**SNOMED semantic tags**: (disorder)=disease, (finding)=clinical obs incl. social
determinants, (situation)=admin. Top "condition" is admin ("medication review due").
Social determinants (isolation, unemployment) are predictive of readmission — keep
them, exclude admin codes, when building comorbidity features.

**Critical-eye on synthetic analytics**: trust the pipeline, question the numbers.
Bimodal readmission curve revealed Synthea's generative model. Don't quote synthetic
rates as epidemiological fact.

**dbt build**: runs models + snapshots + tests in DAG order — the canonical "reproducible
from clone" verification.
