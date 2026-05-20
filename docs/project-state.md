# Project State — End of Phase 4

Last updated: 2026-05-19. Phase 4 complete. Phases 1–4 of 11 done.

## Project Context

Hospital 30-day readmission risk lakehouse on Azure. Cross-industry parallel = churn.
Owner: Ibrahim Al-Hindi (data scientist + CPA, transitioning to data engineer).
Budget: $500. Timeline ceiling: 3 weeks. Repo: github.com/ibralhindi/readmission-lakehouse (public).

## Tech Stack (locked)

Python 3.12 + uv + ruff + mypy (pragmatic-strict). Synthea FHIR R4 Bulk Export NDJSON, 10k MA patients seed=42. Azure australiaeast. Terraform 1.15 + azurerm 4.x + azuread 3.x + databricks 1.x. Databricks Premium SKU. PySpark 3.5 + delta-spark 3.2 on Databricks Runtime 17.3 LTS. LangGraph for agentic AI (Phase 8). OpenAI API direct + Chroma local vector store. Power BI Desktop. dbt with snapshots for SCD2. Airflow 3.x local Docker (Phase 7).

## Working Agreements (unchanged)

Tier scaffolding A/B/C. End-of-phase project-state snapshots + quizzes + decisions log. WHY-not-WHAT comments. AI collaboration disclosed honestly in README. See `.cursor/rules/*.mdc`.

## Repo Structure
readmission-lakehouse/
├── .cursor/rules/                          # Cursor behaviour rules
├── .github/workflows/terraform.yml         # OIDC CI/CD
├── databricks.yml                          # Asset Bundle root config
├── resources/
│   └── bronze_ingestion.yml                # Bronze job (for_each_task, 14 resources)
├── dist/                                   # Built wheels (gitignored)
├── scripts/{setup-phase3-*, upload-synthea-to-adls}.sh
├── terraform/environments/dev/
│   ├── {main, variables, locals, outputs, rg, storage, keyvault, databricks, identity}.tf
│   └── uc.tf                               # Unity Catalog: SC, EL, catalog, schemas
├── src/readmission_lakehouse/
│   ├── bronze/
│   │   ├── cli.py                          # Console-script entry point (rl-bronze-ingest)
│   │   ├── ingest.py                       # add_ingestion_metadata + ingest_resource
│   │   └── resources.py                    # BronzeResource dataclass + 14 entries
│   ├── contracts/fhir.py                   # Pydantic v2 FHIR contracts (6 resources)
│   └── tools/{profile_synthea, sample_synthea}.py
├── tests/
│   ├── conftest.py                         # Session-scoped local Spark fixture
│   └── unit/bronze/test_ingest.py          # 7 tests on add_ingestion_metadata
├── data/synthea/output/                    # Local FHIR NDJSON (37 GB, gitignored)
├── docs/{data-dictionary, decisions, quiz-log, project-state}.md
└── pyproject.toml                          # [project.scripts] rl-bronze-ingest

## Live Azure Resources

### Phase 3 carryover

| Resource | Name | Notes |
|---|---|---|
| RG project | `rl-rg-dev` | australiaeast |
| RG tfstate | `rl-rg-tfstate` | Bootstrap-only |
| RG dbx-managed | `rl-rg-dev-dbx-managed` | Azure-managed |
| Storage (project) | `rlst3e33` | ADLS Gen2 + HNS, Standard_LRS |
| Storage (tfstate) | `rltfstate3e33` | Blob versioning on |
| Key Vault | `rl-kv-3e33` | RBAC auth |
| DBX workspace | `rl-dbx-3e33` | Premium |
| Access Connector | `rl-ac-3e33` | System-assigned MI |
| AAD App (CI) | `rl-gh-actions-dev` | OIDC, no secret |

### Unity Catalog (Phase 4)

| Resource | Name |
|---|---|
| Metastore | `metastore_azure_australiaeast` (auto-created, empty-root) |
| Storage credential | `rl-access-connector-dev` (wraps rl-ac-3e33) |
| External locations | `rl-{bronze,silver,gold,raw}-dev` |
| Catalog | `rl_dev` (Terraform-managed, ISOLATED) |
| Schemas | `rl_dev.{bronze,silver,gold}` (per-schema managed_location) |
| Default catalog | `rl_dbx_3e33` (auto-created, unused but harmless) |

Catalog default storage: `abfss://raw@.../_catalog_default` (rarely written; schemas override).

### Databricks job (Phase 4)

| Resource | Name | Notes |
|---|---|---|
| Job | `[dev ibralhindi@gmail.com] bronze-ingestion` | for_each_task, 14 iterations |
| Job cluster | `bronze_cluster` (DBR 17.3 LTS, DS3_v2, single-node) | Ephemeral; reused across iterations within a run |

## Data Inventory

### Raw layer (`abfss://raw@rlst3e33.../synthea/`)

14 gzipped NDJSON files, total ~1.13 GB compressed (~13× compression from 15 GB uncompressed). gzip is single-task on read (non-splittable); fine for single-node cluster, would migrate to bzip2 or Parquet for distributed scale.

### Bronze layer (`rl_dev.bronze.*`)

All 14 tables loaded. Total ~11.3M rows. Schema: inferred FHIR struct + 4 metadata columns.

| Table | Rows |
|---|---|
| patient | 11,423 |
| organization | 1,141 |
| practitioner | 1,141 |
| encounter | 664,623 |
| document_reference | 664,623 |
| condition | 412,692 |
| procedure | 1,848,211 |
| observation | 5,862,543 |
| medication_request | 573,225 |
| immunization | 164,146 |
| claim | 1,237,848 |
| allergy_intolerance | 10,468 |
| care_plan | 37,736 |
| care_team | 37,736 |

Metadata columns: `_load_ts` (timestamp), `_source_file` (input_file_name), `_row_hash` (sha2 of original cols as JSON, 64-char hex), `_ingestion_run_id` (e.g. `bronze_20260519T142055Z`).

## Phase Status

- [COMPLETED] Phase 1 — Scaffolding
- [COMPLETED] Phase 2 — Synthea generation + Pydantic FHIR contracts
- [COMPLETED] Phase 3 — Azure infra via Terraform + OIDC CI/CD
- [COMPLETED] Phase 4 — Bronze ingestion (UC + asset bundle + 14 Delta tables)
- [PENDING] Phase 5 — Silver layer (Pydantic-validated cleansed conformed)
- [PENDING] Phase 6 — Gold layer (Kimball star: FactEncounter, FactReadmission, dims)
- [PENDING] Phase 7 — Airflow orchestration (3.x local Docker)
- [PENDING] Phase 8 — RAG / LangGraph Care Manager Agent + Streamlit demo
- [PENDING] Phase 9 — Power BI dashboard
- [PENDING] Phase 10 — CI/CD enhancements + dbt
- [PENDING] Phase 11 — Final README + AI-collaboration framing

## Cost Tracker

| Phase | Spend | Note |
|---|---|---|
| 1–3 | <$1 | Storage idle, no compute |
| 4 | ~$2 | One cluster boot for full ingest + smoke tests; rest is storage |
| **Total to date** | **~$3** | Of $500 budget |

Storage ongoing: ~$0.30/month for 15 GB compressed + Delta footprint. Trivial.

## Key Interview Talking Points (Phase 4 additions)

**FHIR + Synthea**:
- Bronze scope: 14 of 22 resources. Deferred 8 (EOB 9.9G redundant with Claim, etc.)
- Observed cardinalities: care_plan = care_team (1:1), doc_ref = encounter (Synthea generates 1:1), org = practitioner (1:1, Synthea simplification — real ratio is many:1)
- SNOMED CT not ICD-10 (AU Digital Health Agency standard)

**Compression at the raw layer**:
- gzip NDJSON in raw: ~13× compression vs uncompressed (15GB → 1.13GB)
- Spark reads .gz transparently. Caveat: gzip non-splittable, 1 file = 1 task. Fine for single-node; distributed scale = bzip2 (splittable) or Parquet with snappy.

**Bronze metadata model**:
- 4 columns: `_load_ts`, `_source_file`, `_row_hash`, `_ingestion_run_id`
- `_row_hash` = SHA-256 of original-columns struct serialised to JSON (sha2(to_json(struct(*cols)), 256))
- Computed BEFORE metadata cols added — same source row produces same hash across runs, enabling future MERGE-based incremental ingest without code change
- Today: overwrite mode (snapshot ingest, idempotent); upgrade path: MERGE on FHIR `id` comparing `_row_hash`

**Unity Catalog architecture**:
- Empty-root metastore + schema-level managed_location: avoids Premium-tier storage account requirement
- Each schema's managed_location is a subpath of its layer's external_location
- Catalog default storage at `raw/_catalog_default` — required by API even though our schemas override; underscore prefix signals "infra not data"
- Why our own catalog (`rl_dev`) vs auto-created `rl_dbx_3e33`: control over storage location, project-named, separate from workspace-default

**Databricks development workflow**:
- Python package + wheel + asset bundle beats notebooks for production pipelines: diffable in PRs, locally testable with pytest, type-checked with mypy
- Notebooks reserved for exploration / ad-hoc validation
- `python_wheel_task` with console_scripts entry point — proper Python packaging

**Asset bundle design**:
- `databricks.yml` at root, `resources/*.yml` for jobs/pipelines
- `artifacts.python_wheel` with `build: uv build --wheel` — bundle handles build+upload automatically
- Job cluster, not interactive — auto-terminates after task completes, no manual cleanup discipline needed
- `for_each_task` with `concurrency: 1` and shared `job_cluster_key` — 14 ingestions on one cluster boot (~$2 total vs ~$15 if each iteration booted its own cluster)
- Targets (dev/staging/prod): `mode: development` prefixes job names with developer identity

**`.save()` vs `.saveAsTable()` (real bug we caught)**:
- `.save(path)` writes to a file path; `.saveAsTable(name)` writes AND registers in the metastore
- In UC, only `.saveAsTable` routes data into the schema's managed_location and exposes the table through the three-level namespace
- `.save()` would create orphan files invisible to UC

**Performance gotcha (also caught)**:
- `df.count()` after `df.write` recomputes the entire DAG (lazy)
- `spark.table(target).count()` reads from Delta statistics (instant) AND validates write committed

**MSA-as-guest-user UPN quirk** (hit twice in this project):
- Personal Microsoft accounts as Azure AD guests get synthetic UPN: `<email-with-_>#EXT#@<tenant>.onmicrosoft.com`
- azcopy needed `AZCOPY_AUTO_LOGIN_TYPE=AZCLI` to bypass its OAuth client
- Databricks account console needed the UPN form directly
- Both failures look like permission errors; root cause is sign-in flow incompatibility, not RBAC

**CLI vs UI for one-time vs reproducible ops**:
- Metastore creation: UI is correct (one-time, account-level, auth complexity not worth automating for portfolio scale)
- Storage credential, external locations, catalog, schemas: Terraform databricks provider — reproducible, version-controlled, idempotent

**`databricks fs ls abfss://`** doesn't work — CLI's fs commands are for DBFS and UC Volumes only. Use `az storage blob list` for direct cloud URL inspection.
