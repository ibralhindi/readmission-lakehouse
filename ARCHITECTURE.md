# Architecture & Project Context — Readmission Lakehouse

> **Purpose.** This is the deep-reference companion to the README. It exists for two audiences: a human who wants the full mental model of the project, and an LLM given this document *alongside the codebase* so it has complete context to reason about or extend the project.
>
> **How to use it.** This document deliberately does **not** reproduce file contents — the code is the source of truth for *what* each file does; read the files for that. This document captures what the code can't tell you on its own: the architecture intent, how the pieces relate, and the **reasoning and trade-offs** behind each decision. Where a snippet appears, it's only to illustrate a non-obvious pattern. If anything here ever conflicts with the code, the code wins and this document is the bug.

---

## 1. What the project is

A production-style data-engineering platform on a Databricks lakehouse. It ingests synthetic FHIR R4 clinical records, lands them through a governed medallion pipeline (bronze → silver → gold), models them into a tested Kimball-style dimensional warehouse, orchestrates the run with Airflow, and serves the result two ways: a Power BI dashboard and a deployed, zero-secrets agentic-RAG assistant that drafts a readmission-risk brief for a patient.

The clinical use case — predicting and explaining 30-day hospital readmissions — is a stand-in for a pattern that recurs across industries: **predict and explain a costly repeat event from an entity's event history** (churn, fraud, asset failure). The engineering is the point; the clinical finding (a defensible 13.64% transfer-excluded readmission rate over 12,689 index admissions) is evidence the pipeline works end to end.

---

## 2. Architecture & data flow

```
Synthea (FHIR R4, seed 42, pop 10,000, Massachusetts)
        │  generate + upload
        ▼
ADLS Gen2 (raw NDJSON)
        │  bronze-ingestion Databricks job (PySpark, for_each over 14 resources)
        ▼
Bronze  (rl_dev.bronze.*)            — raw fidelity, schema-on-read, ingestion metadata
        │  silver-validation Databricks job (PySpark + Pydantic contracts)
        ▼
Silver  (rl_dev.silver.*_valid / *_quarantine, then dbt silver models)
        │  dbt build
        ▼
Gold    (rl_dev.gold.*)              — Kimball star schema, SCD2 dimensions
        │
        ├──► Power BI (Import mode, over gold)
        └──► RAG agent (LangGraph, reads gold via SQL warehouse + Chroma)

Orchestration : Airflow DAG `readmission_pipeline`  (bronze → silver → dbt)
Provisioning  : Terraform (modular)                 (all Azure + Databricks resources)
Governance    : Unity Catalog                        (catalog/schemas, external locations, storage credentials)
CI/CD         : GitHub Actions                        (lint/type/test/dbt-parse + terraform fmt/validate)
Deployment    : Docker → ACR → Azure Container Apps   (agent, under a managed identity)
```

The **medallion layers** map to responsibilities, not just storage tiers: bronze preserves the raw record exactly as ingested (so nothing is ever lost), silver is the typed/validated boundary, and gold is the business-ready model. A bad record degrades one row in silver (it's quarantined with a reason) instead of corrupting the warehouse.

---

## 3. Repository map

Annotated index from `git ls-files`. One line per directory and file.

```
readmission-lakehouse/
├── .dockerignore              # Docker build-context excludes (data/, terraform/, dbt/, etc.) — independent of .gitignore
├── .env.example               # Template for Azure/Databricks/OpenAI env vars (local dev; secrets not committed)
├── .github/                   # GitHub Actions CI/CD
│   └── workflows/
│       ├── ci.yml             # Push/PR: ruff lint+format, mypy, pytest (60% cov gate), dbt parse (offline)
│       └── terraform.yml      # Terraform path-filtered: fmt check + init -backend=false + validate
├── .gitignore                 # Git ignore rules (venv, .chroma, data outputs, tfstate, etc.)
├── .pre-commit-config.yaml    # Local hooks: whitespace/YAML, ruff, mypy, terraform fmt/validate
├── .python-version            # Pins Python 3.12 for uv/pyenv
├── Dockerfile                 # Multistage agent image: uv sync rag group, COPY src + baked .chroma, Streamlit on 8501
├── LICENSE                    # Project license
├── Makefile                   # install/lint/format/test/test-dags/clean/tree developer shortcuts
├── README.md                  # Portfolio overview, quickstart, headline metrics, screenshots
├── databricks.yml             # Databricks Asset Bundle root: wheel artifact, dev target, job permissions for Airflow SP
├── pyproject.toml             # uv project: deps, console scripts, ruff/mypy/pytest/coverage config
├── uv.lock                    # Locked dependency versions for reproducible uv sync
│
├── airflow/                   # Local Airflow 3 stack (Docker) orchestrating the medallion refresh
│   ├── .env.example           # Template for Airflow-specific env (Fernet key, UID, etc.)
│   ├── .gitignore             # Airflow-local ignore rules
│   ├── Dockerfile             # Extends apache/airflow:3.2.1 with Databricks provider + dbt-databricks
│   ├── docker-compose.yaml    # CeleryExecutor Airflow cluster (Postgres, Redis, webserver, scheduler, worker)
│   ├── requirements.txt       # Extra pip deps baked into the Airflow image (Databricks provider, dbt, pytest)
│   ├── dags/
│   │   └── readmission_pipeline.py  # DAG: trigger_bronze >> trigger_silver >> run_dbt_build (manual schedule)
│   ├── dbt-profiles/
│   │   ├── .user.yml          # dbt local user config (machine-specific; tracked for Airflow mount)
│   │   └── profiles.yml       # dbt Databricks profile for the `airflow` target (SP OAuth via env vars)
│   ├── plugins/
│   │   └── .gitkeep           # Placeholder for optional Airflow plugins
│   └── tests/
│       └── test_dag_integrity.py    # Asserts DAG imports, task chain, retries, manual schedule
│
├── data/                      # Local/generated data (mostly gitignored; placeholders + Synthea config in git)
│   ├── guidelines/
│   │   └── .gitkeep           # Reserved for optional local guideline source files
│   └── synthea/
│       ├── .gitkeep           # Reserved for Synthea FHIR NDJSON output (actual data gitignored)
│       └── synthea.properties # Synthea generator config (seed 42, MA, 10k population, FHIR NDJSON export)
│
├── dbt/                       # dbt project: silver flattening, SCD2 snapshots, gold star schema
│   ├── .gitignore             # Ignores target/, dbt_packages/, logs
│   ├── dbt_project.yml        # Project config: readmission_dbt profile, silver/gold schema routing
│   ├── packages.yml           # Declares dbt_utils dependency
│   ├── package-lock.yml       # Pinned dbt_utils version from last dbt deps
│   ├── analyses/
│   │   └── .gitkeep           # Placeholder for ad-hoc dbt analyses
│   ├── seeds/
│   │   └── .gitkeep           # Placeholder for CSV seeds (none used yet)
│   ├── tests/
│   │   └── .gitkeep           # Placeholder for custom data tests (YAML tests used instead)
│   ├── macros/
│   │   ├── extract_fhir_id.sql       # Parse FHIR reference strings to bare resource IDs
│   │   ├── generate_schema_name.sql  # Override so +schema: silver/gold land in rl_dev.silver/gold
│   │   └── parse_fhir_timestamp.sql  # Safe ISO-8601 FHIR datetime → Spark timestamp
│   ├── models/
│   │   ├── silver/
│   │   │   ├── _sources.yml           # bronze + silver_validated source declarations
│   │   │   ├── _silver_models.yml     # Column tests/docs for silver models
│   │   │   ├── patient.sql            # Flatten validated Patient → tabular silver.patient
│   │   │   ├── encounter.sql          # Flatten validated Encounter → tabular silver.encounter
│   │   │   ├── condition.sql          # Flatten validated Condition → tabular silver.condition
│   │   │   ├── procedure.sql          # Flatten validated Procedure → tabular silver.procedure
│   │   │   ├── organization.sql       # Flatten validated Organization → tabular silver.organization
│   │   │   ├── practitioner.sql       # Flatten validated Practitioner → tabular silver.practitioner
│   │   │   ├── observation.sql        # Flatten bronze Observation (no contract yet); incremental merge
│   │   │   └── medication_request.sql # Flatten bronze MedicationRequest (no contract yet)
│   │   └── gold/
│   │       ├── _gold_models.yml       # Column tests/docs for gold dimensions and facts
│   │       ├── dim_date.sql           # Calendar date dimension (1900–2030 spine, YYYYMMDD keys)
│   │       ├── dim_patient.sql        # SCD2 patient dimension from patient_snapshot
│   │       ├── dim_organization.sql   # SCD2 organization dimension from organization_snapshot
│   │       ├── dim_provider.sql       # SCD2 practitioner dimension from practitioner_snapshot
│   │       ├── dim_condition.sql      # Deduplicated SNOMED condition reference dimension (not SCD2)
│   │       ├── fact_encounter.sql     # One row per encounter; as-of patient join, current org join
│   │       └── fact_readmission.sql   # One row per IMP index admission; 30-day readmission flags
│   └── snapshots/
│       ├── patient_snapshot.sql       # SCD2 check snapshot on patient demographics
│       ├── organization_snapshot.sql  # SCD2 check snapshot on organization attributes
│       └── practitioner_snapshot.sql  # SCD2 check snapshot on practitioner attributes
│
├── docs/                      # Supplementary documentation and visuals
│   ├── data-dictionary.md     # Per-FHIR-resource field inventory and bronze/silver/gold plans
│   ├── star_schema_dbml       # dbdiagram.io DBML source for the gold star schema
│   ├── Star_Schema.png        # Rendered star-schema diagram
│   ├── PowerBI_Dashboard_Screenshot.png  # Power BI dashboard screenshot
│   └── agent_screenshot.png   # Streamlit agent UI screenshot
│
├── resources/                 # Databricks Asset Bundle job definitions (included by databricks.yml)
│   ├── bronze_ingestion.yml   # for_each over 14 FHIR resources → rl_dev.bronze.* via rl-bronze-ingest
│   └── silver_validation.yml  # for_each over 6 contracted resources → *_valid / *_quarantine
│
├── scripts/                   # Bootstrap and operational shell scripts
│   ├── setup-tools.sh         # Install Azure CLI, Terraform, tflint on Debian/WSL
│   ├── setup-azure.sh         # Verify az login, register providers, write terraform.tfvars suffix
│   ├── setup-tf-backend.sh    # Bootstrap remote Terraform state RG + storage (chicken-and-egg)
│   ├── upload-synthea-to-adls.sh  # azcopy upload of 14 Synthea NDJSON files to ADLS raw/synthea
│   └── smoke_rag.py           # End-to-end OpenAI embed → Chroma store/retrieve smoke test
│
├── src/readmission_lakehouse/ # Main Python package
│   ├── __init__.py            # Package version string
│   ├── contracts/             # Pydantic FHIR contracts (silver typed boundary)
│   │   ├── __init__.py        # Package marker
│   │   └── fhir.py            # Six resource contracts + RESOURCE_REGISTRY
│   ├── bronze/                # PySpark raw FHIR → bronze Delta ingestion
│   │   ├── __init__.py        # Package marker
│   │   ├── resources.py       # BRONZE_RESOURCES catalogue (14 FHIR types, globs, table names)
│   │   ├── ingest.py          # spark.read.json + four provenance metadata columns → Delta overwrite
│   │   └── cli.py             # Databricks job entry point rl-bronze-ingest (--resource-name)
│   ├── silver/                # PySpark Pydantic validation → valid/quarantine split
│   │   ├── __init__.py        # Package marker
│   │   ├── resources.py       # SILVER_VALIDATIONS catalogue (6 contracted bronze tables)
│   │   ├── validate.py        # UDF validates rows; quarantines only ValidationError failures
│   │   └── cli.py             # Databricks job entry point rl-silver-validate (--resource-name)
│   ├── tools/                 # Local Synthea sampling/profiling utilities (no Spark)
│   │   ├── __init__.py        # Package marker
│   │   ├── sample_synthea.py  # CLI: deterministic downsample of NDJSON to a patient subset
│   │   └── profile_synthea.py # CLI: Markdown summary of local Synthea NDJSON shape/coverage
│   └── agent/                 # LangGraph RAG care-manager assistant
│       ├── .env.example       # Non-secret Databricks host/path/client-id template for local agent
│       ├── __init__.py        # Package marker
│       ├── config.py          # Model names, Chroma paths, Key Vault secret resolution
│       ├── db.py              # Databricks SQL warehouse queries via SP OAuth M2M
│       ├── profile.py         # Structured patient profile SQL from gold (no comorbidities)
│       ├── corpus.py          # Build Chroma patient_notes + guidelines collections from warehouse/bronze
│       ├── guidelines.py      # Curated copyright-clean transitional-care intervention summaries
│       ├── graph.py           # LangGraph tool-calling agent (3 tools) + run_agent()
│       └── app.py             # Streamlit UI: cohort picker, profile, agent brief + tool trace
│
├── terraform/                 # Modular IaC for Azure + Databricks + agent hosting
│   ├── modules/
│   │   ├── storage/           # Reusable ADLS Gen2 storage account module
│   │   │   ├── .terraform.lock.hcl  # Provider lock file for this module
│   │   │   ├── main.tf        # StorageV2 + HNS account and blob containers
│   │   │   ├── variables.tf   # Module inputs (name, RG, containers, tags)
│   │   │   └── outputs.tf     # Module outputs (id, name, dfs endpoint)
│   │   ├── keyvault/          # Reusable Key Vault module (RBAC mode)
│   │   │   ├── .terraform.lock.hcl
│   │   │   ├── main.tf        # Standard SKU vault with soft delete
│   │   │   ├── variables.tf   # Module inputs
│   │   │   └── outputs.tf     # Module outputs (vault id, URI)
│   │   ├── databricks/        # Reusable Databricks workspace + access connector module
│   │   │   ├── .terraform.lock.hcl
│   │   │   ├── main.tf        # Premium workspace, access connector MI, storage RBAC
│   │   │   ├── variables.tf   # Module inputs
│   │   │   └── outputs.tf     # Module outputs (workspace URL, connector principal)
│   │   └── identity/          # Reusable Entra app + SP + GitHub OIDC federated creds module
│   │       ├── .terraform.lock.hcl
│   │       ├── main.tf        # AAD application, service principal, federated credentials
│   │       ├── variables.tf   # Module inputs
│   │       └── outputs.tf     # Module outputs (application/client ids)
│   └── environments/
│       └── dev/               # Dev environment root module (composes modules + app/UC resources)
│           ├── .terraform.lock.hcl      # Provider lock file for dev stack
│           ├── main.tf          # Terraform/backend/provider requirements
│           ├── variables.tf     # Dev input variables (prefix, suffix, tenant, subscription)
│           ├── locals.tf        # Computed resource names (RG, storage, KV, workspace, etc.)
│           ├── terraform.example.tfvars  # Example tfvars (copy to terraform.tfvars locally)
│           ├── rg.tf            # Main Azure resource group
│           ├── storage.tf       # storage module + developer blob contributor grant
│           ├── keyvault.tf      # keyvault module + developer KV administrator grant
│           ├── databricks.tf    # databricks module wiring
│           ├── identity.tf      # identity module + CI SP role assignments on RG/KV/tfstate
│           ├── uc.tf            # Unity Catalog credential, external locations, catalog, schemas
│           ├── container_app.tf # ACR, agent MI, Log Analytics, Container Apps env + agent app
│           └── outputs.tf       # Exported endpoints/IDs (storage, KV, UC, agent URL, CI OIDC ids)
│
└── tests/                     # pytest suite (unit + integration placeholder)
    ├── __init__.py            # Package marker
    ├── conftest.py            # Session-scoped local SparkSession fixture
    ├── integration/
    │   └── .gitkeep           # Placeholder for future integration tests
    └── unit/
        ├── __init__.py        # Package marker
        ├── test_smoke.py      # Package import/version smoke test
        ├── test_fhir_contracts.py   # Pydantic contract validation and registry tests
        ├── test_sample_synthea.py   # Synthea sampler CLI behavior tests
        ├── test_profile_synthea.py  # Synthea profiler CLI/statistics tests
        ├── bronze/
        │   ├── __init__.py
        │   └── test_ingest.py       # Bronze metadata column and row-hash tests
        ├── silver/
        │   ├── __init__.py
        │   └── test_validate.py     # Silver validation UDF valid/quarantine behavior tests
        └── agent/
            ├── __init__.py
            ├── test_config.py       # Secret resolution and default config tests
            └── test_profile.py      # Patient profile UUID validation tests
```

---

## 4. Component deep-dives

Each entry: what it is, the key files, and the reasoning. Read the files for the implementation.

**Bronze — ingestion.** A PySpark job (`src/.../bronze/`, run as the `bronze-ingestion` Databricks job, one task with a `for_each` over the 14 selected FHIR resources) reads raw NDJSON from ADLS via `spark.read.json` and writes Delta tables under `rl_dev.bronze.*`, adding ingestion-metadata columns (`_load_ts`, `_source_file`, `_row_hash`, `_ingestion_run_id`). *Why:* preserve raw fidelity and lineage before any transformation, and keep schema-on-read so an upstream FHIR change can't break ingestion.

**Silver — contracts + validation.** Two stages. First, a PySpark job (`src/.../silver/`, the `silver-validation` Databricks job) validates each record against a Pydantic contract (`src/.../contracts/fhir.py`) and splits output into `*_valid` and `*_quarantine` tables with a failure reason. Then dbt silver models (`dbt/models/silver/*.sql`) flatten the validated FHIR into tabular form. *Why:* a typed boundary catches malformed records early and isolates them (one bad row is quarantined, not propagated). Validation catches `ValidationError` narrowly so genuine code bugs fail loudly instead of being silently quarantined. Only the six entities on the readmission critical path are contracted (see §5); `observation` and `medication_request` read bronze directly (schema-on-read) because they're high-volume, polymorphic, and not on that path.

**Gold — dimensional model.** dbt builds a Kimball star (`dbt/models/gold/`): dimensions `dim_date`, `dim_patient` (SCD2), `dim_organization`, `dim_provider`, `dim_condition`; facts `fact_encounter` (one row per encounter) and `fact_readmission` (one row per inpatient index admission). SCD2 history is captured by dbt snapshots (`dbt/snapshots/`) for patient, organization, and practitioner. *Why:* a star schema is the most query-friendly shape for both the BI layer and the agent, and conformed dimensions let the two facts relate without a direct fact-to-fact join (see §5).

**Orchestration — Airflow.** `airflow/dags/readmission_pipeline.py` chains `trigger_bronze >> trigger_silver >> run_dbt_build`. The two job triggers are `DatabricksRunNowOperator`s (by `job_id`); dbt runs in a `BashOperator`. Auth is the `databricks_default` connection (service-principal OAuth M2M); the SP secret comes from an Airflow Variable, the client id is non-secret. `schedule=None` (manual-trigger portfolio DAG). *Why:* see the cost-safety and stability decisions in §5 — this DAG is more than glue.

**IaC — Terraform.** Modular (`terraform/modules/{storage,keyvault,databricks,identity}`), composed in `terraform/environments/dev` — which also defines Unity Catalog, the agent Container App, and ACR inline, not only via modules. *Why:* everything-as-code, reproducible, reviewable; modules keep the resource graph readable and reusable.

**Governance — Unity Catalog.** Metastore → catalog `rl_dev` → schemas `bronze`/`silver`/`gold`; access via external locations + storage credentials (the access connector's managed identity), not storage account keys. *Why:* least-privilege, no long-lived keys in configs, governed lineage.

**The agent.** A true tool-calling LangGraph agent (`src/.../agent/graph.py`) with three tools: a structured patient profile from gold via the Databricks SQL warehouse (`profile.py`), semantic search over the patient's clinical notes, and search over evidence-based guidelines (both backed by Chroma collections built in `corpus.py`). It drafts a cited brief with `gpt-4o-mini`. *Why:* see §5 — the agentic design, the corpus choices, and the decision-support framing are all deliberate.

**CI/CD.** `.github/workflows/ci.yml` runs ruff lint + format check, mypy, pytest (60% coverage gate), and `dbt parse` (offline, no warehouse creds); `terraform.yml` runs fmt + validate. *Why:* gate every push cheaply; `dbt parse` validates model graph validity without a live warehouse.

**Deployment.** Multistage Docker image (BuildKit-free, bakes the `.chroma` vector store) → ACR → Azure Container Apps, running under a user-assigned managed identity. See §5 for the zero-secrets and scale-to-zero reasoning and §8 for the deployment gotchas.

---

## 5. Design decisions & rationale

The heart of the document — what was chosen, why, what the alternative was, and the trade-off. These are the things to be able to defend.

**Medallion architecture (bronze/silver/gold).** *Why:* separate raw fidelity, validation, and business modelling so each layer has one job and failures are contained. *Trade-off:* more tables and more compute than transforming raw → final in one shot, bought for debuggability, lineage, and the ability to reprocess silver/gold without re-ingesting.

**Pydantic data contracts on critical-path entities only.** *Why:* a typed boundary that quarantines-with-reason at silver. The six contracted entities (Patient, Encounter, Condition, Procedure, Organization, Practitioner — the `RESOURCE_REGISTRY` in `contracts/fhir.py`) are the ones the readmission model depends on. *Alternative considered:* contract everything. *Trade-off:* `observation` and `medication_request` pass through schema-on-read because they're high-volume and polymorphic (`value[x]`), and contracting them is cost without payoff for this use case. The honest scope boundary is documented, not hidden.

**Narrow exception handling in validation (`except ValidationError`, not `except Exception`).** *Why:* a contract violation should quarantine; a `KeyError` in our own code is a bug and should crash the job. Catching broadly would silently quarantine real bugs as "bad data."

**Kimball star schema for gold.** *Why:* the most query-friendly shape for BI and for the agent's SQL. *Alternative:* one wide table. *Trade-off:* joins at query time, bought for conformed dimensions and clean grain.

**SCD2 + as-of (point-in-time) join.** `fact_encounter` joins each encounter to the `dim_patient` version whose validity window contains the admission time, so a fact reflects the dimension *as it was when the event happened*. *Why:* point-in-time correctness — the entire payoff of keeping SCD2 history. *Mixed pattern, deliberately:* `dim_organization` uses a current-version join (orgs are stable in this data; point-in-time org attributes add no value), and the practitioner join is deferred because encounters reference practitioners by NPI rather than resource id (joining needs NPI extraction on both sides). Knowing where as-of matters and where it doesn't is the senior call.

**Transfer-excluded readmission rate as the headline.** `fact_readmission` flags same-day next-admissions as likely inter-facility transfers and offers a transfer-excluded rate (13.64%) alongside the raw rate (19.28%). *Why:* CMS folds transfers into the index stay; counting them as readmissions overstates the rate by ~5.6 points. The exclusion is what makes the number defensible.

**Facts relate through conformed dimensions, not fact-to-fact.** Both facts carry `patient_key` and date keys, so they connect via `dim_patient`/`dim_date`. `fact_readmission.index_encounter_key` is a *degenerate reference* for drill-through, not an active relationship. *Why:* a direct fact-to-fact relationship creates ambiguous join paths in the BI model. (The dbt build does join `fact_encounter` to populate surrogate keys — that's a build-time lookup, a separate concern from the semantic-model relationship.)

**Airflow DAG that's more than glue.** A per-task `execution_timeout` bounds each task; because the `DatabricksRunNowOperator`s run synchronously (not deferrable), a timed-out task triggers the operator's built-in `on_kill`, which cancels the remote Databricks run so the cluster stops billing; retries use exponential backoff; jobs are triggered by `job_id` (stable across bundle redeploys) not by the dev-mode display name. *Why:* cost-safety and idempotent-friendly orchestration, defensible as design rather than wiring.

**Databricks Asset Bundle for the jobs.** Bronze and silver run as bundle-defined jobs (`resources/*.yml`, `databricks.yml`), deployed with `databricks bundle deploy`. *Why:* jobs-as-code — reproducible, versioned, deployable, the analogue of IaC for Databricks workloads.

**Unity Catalog with external locations + storage credentials.** *Why:* governed access without storage account keys in configs; least-privilege via the access connector's managed identity.

**A true tool-calling agent, not a fixed RAG pipeline.** The model is given tools and a goal and decides which to call, formulates its own queries, retrieves again if a pass is thin, and decides when to write. *Why:* demonstrates genuine agentic control flow (the brief asked for a true tool-calling agent). *Framing:* explicit decision-support — it suggests, a clinician decides — which is the responsible posture for clinical content.

**Conditions live in the notes (RAG), not the structured profile.** The gold star has no patient↔condition fact, and the agent's structured profile (`profile.py`) deliberately excludes comorbidities; clinical detail is retrieved from the patient's notes via semantic search. *Why:* it matches the data model and plays to RAG's strength (unstructured clinical text).

**Real clinical notes + synthetic guideline summaries in the corpus.** `corpus.py` embeds the patient's actual `DocumentReference` note text (base64-decoded from bronze) for ~150 inpatient-cohort patients; `guidelines.py` holds original, concise summaries of well-established transitional-care practices. *Why:* real notes enable patient-specific retrieval; the guidelines are written from scratch to stay copyright-clean (a production system would license real guideline sources).

**Zero-secrets deployment via managed identity + Key Vault.** The agent uses `DefaultAzureCredential`, which resolves to a developer login locally and to the attached user-assigned managed identity in the cloud — the *same code path*, no stored bootstrap secret. The identity has exactly two grants (AcrPull to pull the image, Key Vault Secrets User to read the OpenAI key and Databricks SP secret). *Why:* no secret in the image, repo, or container environment; least privilege; one auth model everywhere.

**Scale-to-zero on Container Apps.** `minReplicas = 0` so idle cost is zero. *Trade-off:* a cold start on the first request after idle. A `startup_probe` (TCP 8501, generous failure threshold) plus memory headroom (2 vCPU / 4 GiB) lets the container survive its managed-identity/Key-Vault startup latency, which the default readiness probe was too aggressive for (see §8).

**Python toolchain: uv + ruff + mypy + pre-commit, typed and gated.** *Why:* fast, reproducible installs (uv), one linter/formatter (ruff), real type-checking (mypy, with the pedantic-but-third-party-hostile rules disabled and the bug-catching ones kept), pre-commit hooks installed locally via `make install` (CI runs ruff/mypy directly), and a CI coverage floor. Engineering hygiene that scales.

---

## 6. Conventions

- **Comments explain *why*, not *what*.** The code says what it does; comments capture intent and trade-offs.
- **Contracts accept wire-format FHIR** (camelCase via Pydantic aliases) while the Python side stays snake_case; contracts are `frozen` and `extra="ignore"` so they validate the shape we depend on without re-implementing FHIR.
- **Secrets vs identifiers:** secrets (OpenAI key, Databricks SP secret) are resolved from Key Vault at runtime; non-secret identifiers (warehouse host/path, client id, catalog) come from env/`.env` with sensible defaults. Nothing sensitive is committed.
- **Idempotency where it's cheap:** the notes corpus keys documents by note id (re-runnable upsert); ingestion carries a row hash.
- **Determinism:** Synthea `seed=42` / `clinician_seed=42`; the sampler takes a `--seed`.

---

## 7. Limitations & scope boundaries

Deliberate scope (left) and what a production build would add (right):

| Scoped here | Production would add |
|---|---|
| Single `dev` environment, identifiers in config | Multi-environment promotion (Terraform workspaces, dbt/bundle targets, Airflow Variables/Connections) |
| Contracts on critical-path entities; Observation/MedicationRequest schema-on-read | Full contract coverage with explicit quarantine for every entity |
| Practitioner dimension join deferred (NPI vs resource id) | NPI extraction on both sides to wire up `dim_provider` |
| Synthetic, copyright-clean guideline summaries | Licensed, citable guideline sources |
| Vector store baked into the image | Vector store in managed storage, refreshed on a schedule |
| Public, unauthenticated demo endpoint | Entra ID (EasyAuth) auth + per-user rate limits |
| Descriptive readmission analytics | A trained predictive model with monitoring + feature lineage |

These are a map of the boundary between "demonstrate the engineering" and "operate a production system," not unflagged gaps.

---

## 8. Operational gotchas & lessons (deployment)

Hard-won specifics worth knowing before touching the deployment:

- **`.dockerignore` is not `.gitignore`.** Forgetting to exclude `data/` sent a ~37 GB build context. The `.dockerignore` must exclude data and caches independently.
- **ACR's `az acr build` uses the classic builder** (BuildKit is preview-only), so the Dockerfile is written BuildKit-free (plain `COPY`, pinned `uv`).
- **WSL clock skew breaks `az acr build`'s SAS auth.** The robust path is local `docker build` + `az acr login` + `docker push` (token auth).
- **A lean image surfaces implicit dependencies.** `databricks.sdk` was an implicit dep that only failed once the image was minimal — it's now explicit in the `rag` group.
- **The Container App's default readiness probe is too aggressive** for a container whose startup includes managed-identity + Key Vault reads. Fix: an explicit `startup_probe` (TCP 8501, high failure threshold) plus memory headroom — locally the app had 15 GB, which masked a ~2 GiB OOM that only appeared under the App's limits.
- **An open Streamlit browser tab holds a websocket**, which counts as an active connection and keeps one replica alive. Closing tabs + a cooldown lets it scale to zero. (`minReplicas` null/0 = scale-to-zero in azurerm.)
- **Use a stable ingress FQDN output** (`ingress[0].fqdn`), not a "latest revision" attribute.
- **Register the `Microsoft.App` resource provider** before deploying Container Apps.

---

## 9. Glossary

- **FHIR (R4):** the healthcare data interchange standard; resources include Patient, Encounter, Condition, etc. Synthea exports FHIR NDJSON.
- **Synthea:** an open-source synthetic patient generator (used here with seed 42, Massachusetts, 10,000-patient population).
- **Medallion (bronze/silver/gold):** a layered lakehouse pattern — raw / validated / business-ready.
- **SCD2 (slowly changing dimension, type 2):** keeps history by versioning dimension rows with validity windows (`valid_from`/`valid_to`/`is_current`).
- **As-of join:** joining a fact to the dimension version valid at the event's timestamp (point-in-time correctness).
- **Degenerate reference:** a key carried on a fact that points at another fact for drill-through, not modelled as an active relationship.
- **Index admission:** the admission being evaluated for a subsequent 30-day readmission.
- **IMP:** the FHIR encounter class code for inpatient encounters.
- **RAG:** retrieval-augmented generation — grounding an LLM's output in retrieved documents.
- **Managed identity / `DefaultAzureCredential`:** an Azure identity attached to a resource, resolved by the SDK without a stored secret; the same credential class falls back to a developer login locally.
- **Unity Catalog:** Databricks' governance layer (catalogs, schemas, external locations, storage credentials).
- **Databricks Asset Bundle:** jobs/resources defined as code and deployed with `databricks bundle deploy`.

---

*This document is maintained by hand. When the architecture or a decision changes, update the relevant section here in the same change. If you (an LLM) are reading this alongside the repo and find a claim that the code contradicts, treat the code as authoritative and flag the drift.*
