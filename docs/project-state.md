# Project State — End of Phase 10

Last updated: 2026-05-28. Phase 10 complete. Phases 1–10 of 11 done.

## Project Context
Hospital 30-day readmission lakehouse on Azure + agentic RAG care-manager
assistant + Power BI dashboard, with CI/CD and vaulted secrets.
Cross-industry parallel = churn. Owner: Ibrahim Al-Hindi (data scientist +
CPA → data engineer). Budget $500 (~$22 spent).
Repo: github.com/ibralhindi/readmission-lakehouse (public).

## Tech Stack (locked)
Python 3.12 + uv + ruff + mypy + pre-commit. Synthea FHIR R4, 10k MA patients
seed=42. Azure australiaeast. Terraform 1.15 + azurerm 4.x + databricks 1.x.
Databricks Premium DBR 17.3. PySpark 3.5 + delta-spark 3.2. dbt-databricks 1.12.
Airflow 3.2.1 (local Docker). Agentic RAG: LangGraph + langchain-openai +
langchain-chroma + Chroma + databricks-sql-connector + streamlit. OpenAI
text-embedding-3-small + gpt-4o-mini. Power BI Desktop (Import). Azure SDK
(azure-identity + azure-keyvault-secrets) for runtime secret resolution.
GitHub Actions CI.

## Working Agreements (unchanged)
Tier A/B/C scaffolding. End-of-phase snapshots + quizzes + decisions log.
WHY-not-WHAT comments. No-hallucination rule (honored in Phase 10: verified the
setup-uv action, dbt parse-vs-compile connection behavior, and read the actual
Phase 4.3b Databricks-provider auth config before diagnosing the CI failure).
AI collaboration disclosed in README.

## Repo Structure (Phase 10 additions)readmission-lakehouse/
├── .github/workflows/
│   ├── ci.yml            # NEW: lint (ruff) · types (mypy) · tests (pytest) · dbt parse
│   └── terraform.yml     # MODIFIED: scoped to fmt + validate (was plan/apply via OIDC)
├── .pre-commit-config.yaml   # mypy hook gained azure-identity/keyvault + dbt-sql-connector deps
├── terraform/, dbt/, airflow/, src/, tests/, docs/, scripts/
├── src/readmission_lakehouse/agent/
│   ├── config.py         # MODIFIED: get_secret() via DefaultAzureCredential + Key Vault
│   └── db.py             # MODIFIED: SP secret resolved from Key Vault
├── readmission-dashboard.pbix, docs/screenshots/
├── .env                  # now holds only NON-secret identifiers (host/path/client_id)
├── .chroma/              # gitignored
└── pyproject.toml        # rag group: + azure-identity, azure-keyvault-secrets

## Live Azure / Databricks Resources (unchanged)
RG rl-rg-dev | Storage rlst3e33 | Key Vault rl-kv-3e33 (now holds
`openai-api-key` + `databricks-client-secret`) | DBX rl-dbx-3e33 |
SQL warehouse rl-dbt-warehouse | SP rl-airflow-dev (OAuth M2M) |
CI SP rl-gh-actions-dev (OIDC, Azure-plane scoped). Catalog rl_dev.

## Phases 1–9 (complete; detail in git history + earlier snapshots)
1 Scaffold · 2 Contracts · 3 Infra (Terraform, UC, OIDC CI SP) · 4 Bronze ·
5 Silver · 6 Gold (star; 13.64% excl-transfers headline) · 7 Airflow ·
8 Agentic RAG (tool-calling LangGraph agent + Streamlit) ·
9 Power BI dashboard.

## Phase 10 — Productionise (CI + Key Vault)
### CI (.github/workflows/ci.yml)
- Two jobs on every push/PR: `quality` (ruff lint + ruff format-check + mypy +
  pytest) and `dbt` (dbt deps + dbt parse against a placeholder CI profile).
- No cloud credentials: `dbt parse` validates refs/YAML/the model graph
  offline; only compile/build/test would need the warehouse. Fast + free.
- Branch protection: a ruleset on `main` requires both checks to pass; changes
  now flow through PRs (direct pushes to main are rejected — that surfaced as
  the first lesson that protection was working).

### Key Vault secret resolution
- The two genuine secrets (`openai-api-key`, `databricks-client-secret`) moved
  to Key Vault; the non-secret identifiers (host, http_path, client_id) stay
  in .env. config.get_secret(env_var, kv_name) resolves env-first (CI/local
  override) else Key Vault, cached per process.
- `DefaultAzureCredential` authenticates with NO stored bootstrap secret:
  locally it uses `az login`; in cloud it would use a managed identity — same
  code. Verified end-to-end: the agent runs with both secrets absent from .env.
- Why not a Databricks KV-backed secret scope: nothing inside Databricks
  consumes a secret (jobs use the UC storage credential); all consumers are
  external (Airflow, the agent), so app-side DefaultAzureCredential is the fit.

### Terraform CI scoping (the debugging arc)
- Lock-file churn triggered the existing terraform.yml, whose `plan`/`apply`
  refresh state and read the UC resources in uc.tf. The CI SP is Azure-plane
  scoped (OIDC) and was never granted Databricks workspace/metastore access
  (UC entered Terraform in Phase 4, after the SP was made in Phase 3) →
  "User not authorized" reading the storage credential.
- Resolution: scoped the Terraform CI to `fmt -check` + `validate`
  (`init -backend=false`) — config correctness with no provider API calls, no
  cloud auth. UC plan/apply stays a local admin operation. Deliberate
  least-privilege over auto-apply convenience.

## Phase Status
[COMPLETED] 1–10.  [PENDING] 11 README (capstone).

## Cost Tracker
| Phase | Spend |
|---|---|
| 1–9 | ~$22 |
| 10 (GitHub Actions free for public repos; KV ops negligible) | ~$0 |
| **Total** | **~$22 of $500** |

## Key Interview Talking Points (Phase 10 additions)
- **DefaultAzureCredential = one code path, many identities, zero bootstrap
  secret** (az login locally, managed identity in cloud, OIDC in CI).
- **Secret vs identifier**: vaulted only the two real secrets; left host/path/
  client_id in config. Over-vaulting non-secrets is a smell.
- **CI without the warehouse**: dbt parse validates the model graph offline;
  reserved compile/build for an authed tier. Fast, free, no secrets.
- **Azure-plane vs Databricks-plane privilege boundary**: the Terraform CI
  failure was the model enforcing that the OIDC SP, scoped to Azure, has no
  Unity Catalog rights. Chose to scope CI to validate rather than grant the CI
  identity metastore-admin — least privilege over convenience.
- **Branch protection / required checks** force a PR workflow; green-checked
  PRs in history are themselves a signal.
- **OIDC federated auth** (the CI SP) means no long-lived cloud secret in
  GitHub — the same no-stored-secret discipline as the app side.
