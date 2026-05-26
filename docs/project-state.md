# Project State — End of Phase 7

Last updated: 2026-05-26. Phase 7 complete. Phases 1–7 of 11 done.

## Project Context

Hospital 30-day readmission risk lakehouse on Azure. Cross-industry parallel = churn.
Owner: Ibrahim Al-Hindi (data scientist + CPA → data engineer).
Budget $500. Repo: github.com/ibralhindi/readmission-lakehouse (public).

## Tech Stack (locked)

Python 3.12 + uv + ruff + mypy. Synthea FHIR R4 NDJSON, 10k MA patients seed=42.
Azure australiaeast. Terraform 1.15 + azurerm 4.x + azuread 3.x + databricks 1.x.
Databricks Premium, DBR 17.3 LTS. PySpark 3.5 + delta-spark 3.2. dbt-databricks 1.12
(dbt-core 1.11) + dbt_utils. LangGraph (Phase 8) + OpenAI + Chroma. Power BI (Phase 9).
Apache Airflow 3.2.1 (local Docker, CeleryExecutor).

## Working Agreements (unchanged)

Tier scaffolding A/B/C. End-of-phase snapshots + quizzes + decisions log.
WHY-not-WHAT comments. AI collaboration disclosed in README. No-hallucination rule:
verify project-specific facts against transcript or ask; flag inference vs confirmed.

## Repo Structure (Phase 7 additions)
readmission-lakehouse/
├── databricks.yml                          # + top-level permissions (SP CAN_RUN)
├── resources/{bronze_ingestion,silver_validation}.yml
├── dbt/{dbt_project.yml, packages.yml, macros/, models/{silver,gold}/, snapshots/}
├── airflow/                                # Phase 7
│   ├── Dockerfile                          # apache/airflow:3.2.1 + providers
│   ├── requirements.txt                    # apache-airflow-providers-databricks, dbt-databricks
│   ├── docker-compose.yaml                 # + mounts: ../dbt, ../src, ./dbt-profiles
│   ├── .env                                # AIRFLOW_UID
│   ├── dbt-profiles/profiles.yml           # SP M2M OAuth target 'airflow' -> SQL warehouse
│   └── dags/readmission_pipeline.py        # trigger_bronze >> trigger_silver >> run_dbt_build
├── src/readmission_lakehouse/{bronze,silver,contracts,tools}/
├── tests/unit/{bronze,silver}/
├── docs/{data-dictionary,decisions,quiz-log,project-state}.md
└── pyproject.toml

External (not in repo): ~/.dbt/profiles.yml (local U2M, target dev).

## Live Azure / Databricks Resources

### Carryover (Phases 3–6)
RG rl-rg-dev | Storage rlst3e33 (ADLS Gen2) | Key Vault rl-kv-3e33 |
DBX workspace rl-dbx-3e33 (Premium) | Access Connector rl-ac-3e33 | CI app rl-gh-actions-dev (OIDC).
UC: metastore_azure_australiaeast | catalog rl_dev (ISOLATED) | schemas bronze/silver/gold |
storage cred rl-access-connector-dev | external locations rl-{bronze,silver,gold,raw}-dev.

### Compute
- Cluster rl-dev-interactive (DBR 17.3 LTS, DS3_v2, single-node, DEDICATED/single-user =
  ibralhindi) — interactive/ad-hoc dev ONLY.
- SQL warehouse rl-dbt-warehouse (Serverless, 2X-Small, auto-stop 5min,
  http_path /sql/1.0/warehouses/4cefe31ffc4390a9) — pipeline dbt compute. Multi-tenant.
- Job clusters (ephemeral): bronze_cluster, silver_cluster (single-user = deploying user).

### Jobs (asset-bundle)
- [dev ibralhindi] bronze-ingestion (id 73579121572904) — for_each 14 resources.
- [dev ibralhindi] silver-validation (id 122673186058194) — for_each 6 entities.

### Phase 7 identity + orchestration
- Service principal rl-airflow-dev (app id e305daca-ddaa-4446-a3f4-5c89df23a17c),
  Databricks-managed, OAuth M2M, workspace-assigned. Grants: SELECT on bronze;
  ALL PRIVILEGES on silver+gold; CAN USE on rl-dbt-warehouse; CAN_RUN on both jobs
  (via databricks.yml top-level permissions); CAN RESTART on rl-dev-interactive (vestigial).
- Airflow connection databricks_default (Databricks type, extra {"service_principal_oauth": true},
  login = SP app id, password = SP OAuth secret).
- Airflow Variable databricks_sp_client_secret (SP OAuth secret, for dbt env).
- DAG readmission_pipeline: trigger_bronze >> trigger_silver >> run_dbt_build,
  schedule @daily, catchup=False, kept PAUSED (manual trigger only).

## Data Inventory (unchanged from Phase 6)

Bronze: 14 tables ~11.3M rows. Silver: 8 conformed + 6 _valid/_quarantine pairs + 3 SCD2 snapshots.
Gold star: dim_date, dim_patient (SCD2), dim_provider, dim_organization, dim_condition,
fact_encounter (664,623), fact_readmission (12,689 IMP index admissions).

### Headline analytics
30-day readmission rate: **13.64% (transfer-excluded) / 19.28% (raw)**. Raw double-counts
716 same-day transfers (CMS folds into index stay). Transfer-excluded ≈ real-world ~15%.
Day distribution bimodal (day-0 transfers + days-28-30 Synthea scheduling cluster).

## Phase Status

- [COMPLETED] 1 Scaffold | 2 Contracts | 3 Infra | 4 Bronze | 5 Silver | 6 Gold | 7 Airflow
- [PENDING] 8 RAG/LangGraph agent | 9 Power BI | 10 CI/dbt | 11 README

## Cost Tracker

| Phase | Spend |
|---|---|
| 1–6 | ~$13 |
| 7 | ~$? (confirm — end-to-end run + a duplicate-run partial + dbt-auth retries) |
| Total | ~$? of $500 |

## Key Interview Talking Points (Phase 7 additions)

**Why Airflow over Databricks Workflows**: Airflow orchestrates ACROSS systems (Databricks
jobs + dbt + future APIs) with one schedule/retry/backfill/alert surface; Workflows is
Databricks-only. Demonstrates the orchestration layer as a portable, vendor-agnostic skill.

**Headless auth — service principal OAuth M2M**: U2M browser flow can't work in a container,
so a Databricks-managed SP with an OAuth client_id/secret. Machine identity, scoped, rotatable,
not tied to a person. Airflow operators use it via the connection; dbt uses the same SP via
profiles env vars (client_id not secret — it's an app id; secret from an Airflow Variable).

**Single-user (Dedicated) cluster vs multi-tenant compute (the headline Phase-7 bug)**: dbt
failed with "single-user check failed" — a Dedicated cluster runs all code as one bound
identity, so the SP was rejected at attach even WITH Can Restart. Two orthogonal gates: cluster
ACL (can you touch the compute) vs access mode (whose identity does it run as). Fix: point the
pipeline's dbt at a serverless SQL warehouse (multi-tenant, no single-identity binding,
seconds to start). Clean side effect: dedicated cluster for interactive dev, SQL warehouse for
the pipeline.

**DAB-owned resources lock the UI**: bundle-deployed job permissions can't be set in the UI
("modify bundle sources and redeploy") — granted via top-level `permissions` in databricks.yml.
Job names carry a `[dev <user>]` prefix from `mode: development`; referenced jobs by stable id.

**Airflow 3.x specifics**: services split (api-server, scheduler, dag-processor, triggerer,
worker + postgres + redis); operators moved to apache-airflow-providers-standard
(BashOperator), DAG from airflow.sdk. Custom image bakes providers in (ephemeral containers
lose pip installs). Bind-mount the dbt project so the container runs repo code, not a copy.

**Scheduling footgun**: unpausing a @daily/catchup=False DAG immediately runs the latest
interval; adding a manual trigger double-fired. One run = unpause-only OR `dags test`, not both.

**append_env on BashOperator**: `env` alone wipes PATH so the dbt binary vanishes; append_env=True.
