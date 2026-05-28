# Project State — End of Phase 9

Last updated: 2026-05-28. Phase 9 complete. Phases 1–9 of 11 done.

## Project Context
Hospital 30-day readmission lakehouse on Azure + agentic RAG care-manager
assistant + Power BI analyst dashboard. Cross-industry parallel = churn.
Owner: Ibrahim Al-Hindi (data scientist + CPA → data engineer).
Budget $500 (~$22 spent). Repo: github.com/ibralhindi/readmission-lakehouse (public).

## Tech Stack (locked)
Python 3.12 + uv + ruff + mypy. Synthea FHIR R4 NDJSON, 10k MA patients seed=42.
Azure australiaeast. Terraform 1.15 + azurerm 4.x + azuread 3.x + databricks 1.x.
Databricks Premium, DBR 17.3 LTS. PySpark 3.5 + delta-spark 3.2. dbt-databricks 1.12.
Apache Airflow 3.2.1 (local Docker, CeleryExecutor). Agentic RAG: LangGraph +
langchain-openai + langchain-chroma + Chroma + databricks-sql-connector + streamlit.
OpenAI text-embedding-3-small + gpt-4o-mini. Power BI Desktop (Windows, Import mode).

## Working Agreements (unchanged)
Tier A/B/C scaffolding. End-of-phase snapshots + quizzes (docs/quiz-log.md) +
decisions log (docs/decisions.md). WHY-not-WHAT comments. No-hallucination rule.
AI collaboration disclosed in README.

## Repo Structure (Phase 9 additions)
readmission-lakehouse/
├── databricks.yml, resources/, dbt/, airflow/      # Phases 3-7
├── src/readmission_lakehouse/{bronze,silver,contracts,tools}/   # 4-5
│   └── agent/{config,db,guidelines,corpus,profile,graph,app}.py # 8
├── tests/, scripts/, docs/
├── readmission-dashboard.pbix                       # Phase 9 (saved into WSL repo
│                                                    #   via wslpath -w UNC path)
├── docs/screenshots/                                # dashboard shots for README
├── .env, .chroma/                                   # gitignored
└── pyproject.toml

## Live Azure / Databricks Resources (unchanged)
RG rl-rg-dev | Storage rlst3e33 | KV rl-kv-3e33 | DBX rl-dbx-3e33 (Premium) |
cluster rl-dev-interactive (dev-only) | SQL warehouse rl-dbt-warehouse
(Serverless 2X-Small) — used by Airflow's dbt task, the agent, AND Power BI |
SP rl-airflow-dev (OAuth M2M). Catalog rl_dev / schemas bronze,silver,gold.

## Phases 1–8 (complete; detail in git history + earlier snapshots/decisions.md)
1 Scaffold · 2 Contracts · 3 Infra (Terraform, UC) · 4 Bronze (FHIR ingest) ·
5 Silver (8 dbt models, contracts) · 6 Gold (star: dims + fact_encounter 664k +
fact_readmission 12,689; headline 13.64% excl-transfers / 19.28% raw) ·
7 Airflow (orchestration, retries/timeouts/auto-pause) · 8 Agentic RAG
(tool-calling LangGraph agent over notes + guidelines + warehouse, Streamlit UI).

## Phase 9 — Power BI Analyst Dashboard
- **Connection**: Azure Databricks connector → warehouse rl-dbt-warehouse,
  **Import** mode, **PAT** auth (AAD was the alternative). Loaded gold
  dim_date, dim_patient, dim_organization, fact_encounter, fact_readmission.
  Skipped dim_provider (orphaned — deferred NPI join) + dim_condition (reference).
- **Model**: fact constellation. dim_date + dim_patient → BOTH facts;
  dim_organization → fact_encounter only. NO fact-to-fact link (Power BI
  rejected it as an ambiguous path — the dim_patient↔both-facts loop).
  Role-playing dim_date (admission active, discharge inactive). Marked as date table.
- **dbt change**: added index_length_of_stay_hours to fact_readmission
  (denormalized from fact_encounter) so index LOS is sliceable without joining facts.
- **Measures**: Index Admissions (COUNTROWS); Readmissions (excl. transfers)
  (CALCULATE+filter); Readmission Rate (excl. transfers) + (raw) (DIVIDE).
  **Calc column**: Index LOS Bucket (+ hidden sort column).
- **Dashboard** (one page, dark theme): 4 KPI cards (12,689 / 1,731 / 13.64% /
  19.28%); days-to-readmission distribution (bimodal — day-0 transfer spike
  annotated + day 21-30 cluster); rate by index LOS bucket (non-monotonic,
  3-7 days highest ~28%); rate by gender; rate by race; admissions by year
  (filtered to 1980+).
- **Honesty caveat**: demographic + temporal patterns are Synthea generation
  artifacts, NOT clinical findings — flagged on the page, to be repeated in README.

## Phase Status
[COMPLETED] 1–9.  [PENDING] 10 CI/dbt enhancements + Key Vault hardening | 11 README.

## Cost Tracker
| Phase | Spend |
|---|---|
| 1–6 | ~$13 |
| 7 (Airflow + warehouse) | ~$8 |
| 8 (OpenAI + warehouse) | ~$1 |
| 9 (Power BI Desktop free; warehouse import = cents) | ~$0 |
| **Total** | **~$22 of $500** |

## Key Interview Talking Points (Phase 9 additions)
- **Import vs DirectQuery**: chose Import — static snapshot + serverless
  auto-stopping warehouse + snappy interaction without billing per click.
  Production with live data → DirectQuery or scheduled-refresh Import.
- **Fact constellation**: two facts share conformed dimensions; facts relate to
  dims, never to each other. The ambiguous-path error was the model *enforcing*
  that rule (two paths from dim_patient to fact_readmission).
- **Denormalize onto the grain**: needed index LOS on readmission analysis →
  put the column on fact_readmission (its grain), didn't join facts.
- **Three DAX contexts**: measure (model-level, filter-aware) vs calculated
  column (row-level, stored at refresh) vs visual calculation (visual's output
  grid only — why AVERAGEX over a model table failed there).
- **Role-playing dimension**: one active date relationship; USERELATIONSHIP to
  use the inactive discharge-date relationship inside a specific measure.
- **Synthetic-data honesty**: naming the gender/temporal patterns as Synthea
  artifacts (not epidemiology) is a maturity signal — over-claiming would be the
  failure mode.
