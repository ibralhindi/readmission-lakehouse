# Project State

> Updated at end of each phase. Combined with the original project brief, this doc plus the current chat is sufficient to resume work in a new session.

## Project identity

- **Name**: readmission-lakehouse
- **Goal**: Hospital readmission risk lakehouse on Azure — portfolio project for data scientist → data engineer transition (Melbourne, AU)
- **Business problem**: 30-day readmissions cost US$26B annually and are penalised under CMS HRRP / AU AIHW PPH frameworks. Build a unified platform that consolidates patient/encounter/condition data, computes readmission KPIs, identifies high-risk patients, and equips care managers with evidence-based interventions via a LangGraph agent with RAG over clinical guidelines.
- **Cross-industry parallel**: readmission ≅ churn. Architecture is industry-agnostic.
- **Timeline**: 17–21 working days, 5–6 hrs/day. Hard ceiling 3 weeks.
- **Budget**: $500. Spent through Phase 3: <$1.

## Status

- **Completed**: Phase 1 (scaffolding), Phase 2 (data + contracts), Phase 3 (Azure infra + CI/CD)
- **Current**: Phase 4 — Databricks bronze ingestion
- **Repo**: https://github.com/ibralhindi/readmission-lakehouse (public)
- **Dev environment**: Windows 11 + WSL2 Ubuntu, Cursor IDE (with Python + Terraform + Docker + dbt extensions), Python 3.12, uv

## Tech stack (locked)

| Layer | Choice |
|---|---|
| Language | Python 3.12 (matches Databricks Runtime 17) |
| Package manager | uv |
| Lint / format | ruff |
| Type check | mypy "pragmatic-strict" (disallow_untyped_defs + warn_return_any + no_implicit_optional; not strict mode) |
| Tests | pytest, ≥60% coverage gate |
| Pre-commit | ruff, mypy, large-file guard, terraform_fmt, terraform_validate |
| Source data | Synthea, FHIR R4 Bulk Export NDJSON, 10k MA patients, seed=42 |
| Cloud | Azure (australiaeast) |
| IaC | Terraform 1.15 + azurerm 4.x + azuread 3.x + random 3.x |
| Terraform state | Azure Storage backend with AAD auth, blob versioning, in separate RG |
| CI/CD | GitHub Actions, OIDC federation, no long-lived secrets |
| Containers | Docker (Airflow stack, Phase 7) |
| Processing | Databricks Premium + PySpark, Delta Lake, medallion (bronze/silver/gold) |
| Modelling | Kimball star, dbt with snapshots for SCD2 |
| Orchestration | Apache Airflow 3.x, local Docker, Databricks operator |
| BI | Power BI Desktop |
| LLM | OpenAI API direct (text-embedding-3-small + gpt-4o-mini) |
| Agent framework | LangGraph (stateful agent graph) |
| Agent UI | Streamlit |
| Vector store | Chroma (local) |

## Live Azure resources (deployed by Terraform)

| Resource | Name | Notes |
|---|---|---|
| Resource group (project) | `rl-rg-dev` | Terraform-managed |
| Resource group (tfstate) | `rl-rg-tfstate` | Bootstrap-only, outside Terraform's scope |
| Resource group (Databricks) | `rl-rg-dev-dbx-managed` | Azure-managed, untouchable |
| Storage account (project) | `rlst3e33` | ADLS Gen2 + HNS, Standard_LRS, public network |
| Storage account (tfstate) | `rltfstate3e33` | Standard_LRS, blob versioning, private |
| Storage containers (project) | `bronze`, `silver`, `gold`, `raw` | All private, no anonymous access |
| Key Vault | `rl-kv-3e33` | RBAC auth (not access policies), 7-day soft delete, purge protection off |
| Databricks workspace | `rl-dbx-3e33` | Premium tier (Standard deprecated April 2026) |
| Databricks access connector | `rl-ac-3e33` | System-assigned managed identity |
| AAD application (CI) | `rl-gh-actions-dev` | OIDC federation, no client secret |
| Service principal (CI) | (auto) | Federated to GitHub main branch + PR events |
| Federated credentials | `github-main`, `github-pull-request` | Exact-match subject claims |

## Live RBAC (deployed)

| Principal | Role | Scope |
|---|---|---|
| Developer (user) | Storage Blob Data Contributor | `rlst3e33` |
| Developer (user) | Key Vault Administrator | `rl-kv-3e33` |
| Databricks access connector | Storage Blob Data Contributor | `rlst3e33` |
| CI service principal | Contributor | `rl-rg-dev` |
| CI service principal | Storage Blob Data Contributor | `rltfstate3e33` |
| CI service principal | Storage Blob Data Contributor | `rlst3e33` |
| CI service principal | Reader | `rltfstate3e33` |

## Repository layout (key paths)

```
readmission-lakehouse/
├── .cursor/rules/                # 5 rules: project, python, DE, behaviour, learning-mode
├── .vscode/                      # extensions.json + settings.json (committed)
├── .github/workflows/
│   └── terraform.yml             # OIDC-authenticated plan-on-PR, apply-on-main
├── scripts/
│   ├── setup-phase3-tools.sh     # installs az, terraform, tflint in WSL
│   ├── setup-phase3-azure.sh     # az login verify, register providers, generate suffix, write tfvars
│   └── setup-phase3-backend.sh   # bootstrap tfstate RG/SA/container
├── terraform/
│   ├── environments/dev/
│   │   ├── main.tf               # providers + backend
│   │   ├── variables.tf          # 7 variables
│   │   ├── locals.tf             # resource name composition, common_tags
│   │   ├── outputs.tf            # consolidated outputs incl. CI secrets
│   │   ├── rg.tf                 # main resource group
│   │   ├── storage.tf            # module call + developer RBAC + moved block
│   │   ├── keyvault.tf           # module call + developer RBAC + moved block
│   │   ├── databricks.tf         # module call
│   │   ├── identity.tf           # CI app + SP + federated creds + 4 RBAC assignments
│   │   ├── terraform.example.tfvars  # committed reference
│   │   ├── terraform.tfvars      # gitignored, generated by setup-phase3-azure.sh
│   │   └── backend.conf          # gitignored, generated by setup-phase3-backend.sh
│   └── modules/
│       ├── storage/              # ADLS Gen2 SA + for_each containers
│       ├── keyvault/             # KV with RBAC auth
│       ├── databricks/           # Workspace + access connector + SBDC role assignment
│       └── identity/             # AAD app + SP + federated credentials (map-based for_each)
├── src/readmission_lakehouse/
│   ├── contracts/fhir.py         # Pydantic v2 models for 6 core FHIR resources
│   └── tools/
│       ├── profile_synthea.py    # CLI: NDJSON scanner → markdown data dictionary
│       └── sample_synthea.py     # CLI: 50-patient subset extractor (bug-fixed for Patient/<id> refs)
├── data/synthea/
│   ├── synthea.properties        # reproducibility config
│   └── output/                   # 37G raw NDJSON (gitignored)
├── docs/
│   ├── data-dictionary.md        # 24 resource sections; 14 bronzed, 10 not
│   ├── decisions.md              # architectural decisions in user's own words
│   ├── quiz-log.md               # gitignored — interview prep
│   └── project-state.md          # this file
├── dashboards/                   # Power BI (Phase 9)
├── Makefile                      # install, lint, format, test, clean, tree
└── pyproject.toml                # 3 dep groups: main, dev, rag
```

## Key decisions and rationale (cumulative)

### Foundations (Phase 1–2)
1. **FHIR NDJSON over CSV**: matches HL7 Bulk Data Export spec; nested structure forces real Spark work.
2. **WSL2-first dev**: parity with Linux production runtimes; avoids Windows path/line-ending bugs.
3. **uv + ruff + pragmatic-strict mypy + Pydantic v2**: modern Python toolchain; relaxed from strict-mypy after friction with vendor libs.
4. **Hand-rolled slim FHIR contracts**: validates only what we use; demonstrates contract design.
5. **Bronze plan: 14 of 22 resources**: ExplanationOfBenefit (9.9G), DiagnosticReport (2.8G), Provenance (952M), etc. deferred — redundant with bronzed resources or out of scope.
6. **DocumentReference bronzed** for use as RAG corpus in Phase 8.
7. **SNOMED CT not ICD-10**: Synthea default; matches AU Digital Health Agency standard.
8. **Hospitalization sub-resource sparse (~0.1%)**: readmission detection keys off `class.code IN ('IMP','EMER')` + `period`, not `hospitalization` sub-fields.
9. **Three-tier learning-mode scaffolding**: A=write fully, B=skeleton, C=hints only. User writes core logic.

### Cloud & infrastructure (Phase 3)
10. **Terraform state in its own RG**, never Terraform-managed: lifecycle independence + circular dependency avoidance + team-separation pattern.
11. **AAD auth on backend (`use_azuread_auth = true`)**: no shared keys, audit-attributable.
12. **Standard_LRS for state SA**: cheapest tier; state is recoverable via blob versioning, geo-redundancy adds no value.
13. **ADLS Gen2 `is_hns_enabled = true`**: immutable at creation; enables Delta filesystem semantics.
14. **No `network_rules` block on storage**: `default_action = "Allow"` is unsupported by azurerm (causes recurring drift); for real restrictions declare with `Deny` + ip_rules.
15. **Key Vault RBAC authorization** (not legacy access policies): centralised IAM model.
16. **No purge protection on KV in dev**: lets `terraform destroy` fully reclaim names; flip on for prod.
17. **Databricks Premium SKU**: Standard deprecated April 1 2026; ~20–30% DBU uplift, ≈$3–5 over project lifetime.
18. **Access Connector + system-assigned managed identity** for Databricks→storage: replaces legacy SP+secret pattern.
19. **OIDC federated identity for CI**: cryptographically signed claims, no stored secrets to leak or rotate.
20. **Exact-match subject claims** on federated credentials: `repo:OWNER/REPO:ref:refs/heads/main` and `repo:OWNER/REPO:pull_request`; never wildcards (fork PR attack vector).
21. **Decoupled developer identity from running identity** via `var.developer_object_id` after discovering `data.azurerm_client_config.current` returns different values locally vs CI.
22. **`moved` blocks for resource renames**: identity-preserving refactors, zero churn.

## Working agreements

- Every step gets a one-paragraph "why".
- Non-trivial files/commands/prompts get a breakdown.
- Cursor prompts state tier classification before generating.
- Project-state.md regenerated at end of each phase.
- End-of-phase quiz (5 questions, answered in chat, then saved to `docs/quiz-log.md`).
- Decisions log (`docs/decisions.md`) maintained in user's own words.

## Data inventory

- **Patients**: 11,423 (gender 50/50, deceased 11.8%)
- **Encounters**: 664,623 (predominantly AMB; ~0.8% IMP)
- **Conditions**: 412,692 (SNOMED CT codes)
- **Total Synthea output**: 37 GB (local only, gitignored)
- **Working sample**: 50 patients, 101 MB, local only (gitignored)
- **Committed CI fixture**: deferred to Phase 4 design

## Open issues / deferred decisions

- **Committed CI fixture**: design in Phase 4. Likely 3 patients, bronzed-only, ~3–5 MB total, possibly gzipped.
- **OpenAI API key**: not yet provisioned. Phase 8.
- **Synthea AU geography**: still Massachusetts; defer unless time permits.
- **Production hardening (deferred to a hypothetical Phase 12)**: KV purge protection on, storage network ACLs with Deny + IP allowlist, private endpoints for storage/KV, customer-managed encryption keys.
- **Power BI Pro license**: only needed if publishing online; reassess Phase 9.

## Interview talking points (accumulated)

**Data engineering / modelling**
- FHIR Bulk Export NDJSON over CSV: matches HL7 / 21st Century Cures Act compliance format real EMRs send.
- Made explicit bronze-scope decision: EOB at 9.9 GB would have tripled processing cost for redundant data.
- Found a sampler bug — assumed `urn:uuid:` references, but Synthea uses `Patient/<id>` for cross-resource refs. Caught during integration on full 660k-row Encounter file. Lesson: assumptions about external data formats need verification against actual data, not specs.
- Defaulted to SNOMED CT — aligns with AU Digital Health Agency standard. Would add SNOMED→ICD-10 crosswalk for US workloads.
- Derived readmission from `Encounter.class` + `period` because Synthea's `hospitalization` sub-resource is only populated on 0.1% of records — real-world data is sparser than tutorials suggest.

**Cloud / Terraform**
- State backend in its own RG, outside Terraform scope: lifecycle independence, circular-dependency avoidance, real-team separation-of-concerns.
- Azure management plane vs data plane: Subscription Owner doesn't include Storage Blob Data ops; collided with this three times.
- ADLS Gen2 `is_hns_enabled` is immutable at creation — get it right the first time.
- Hit the well-known azurerm storage `network_rules` drift loop: provider docs explicitly require `default_action = "Deny"` with rules, so omit the block entirely for Allow.
- Pivoted from Standard to Premium Databricks during build (April 2026 deprecation); ~$3–5 cost impact at our scale.
- Access Connector + managed identity pattern replaces legacy SP+secret for Databricks→storage — no secrets in cluster init scripts.

**CI/CD security**
- OIDC federation: credential is derived from cryptographically signed identity claims, not stored. No static token to leak. If federated config is exfiltrated, attacker gets nothing — trust anchored to GitHub's signing keys.
- Exact-match subject claims defend against fork-PR injection (a forked repo can't impersonate the main repo's subject).
- Workflow restricts apply to push:main, plan to pull_request — defence in depth alongside the federated trust.

**Terraform engineering**
- `moved` blocks for resource renames: zero-churn refactors. Without them, role-assignment renames create brief permission gaps + suspicious audit log signatures + recreate-failure risk.
- Decoupled "developer identity" from "whoever runs Terraform" via explicit variable — `data.azurerm_client_config.current` returns different values locally vs CI.
- azurerm 4.x renamed many `enable_*` arguments to `*_enabled` for consistency — caught one stale `enable_rbac_authorization` from documentation drift.

**Python tooling**
- Relaxed mypy from strict to "pragmatic strict" (`disallow_untyped_defs + check_untyped_defs + warn_return_any + no_implicit_optional`): 80% of bug-catching value, 20% of friction with untyped third-party libs.
- `bash set -o pipefail` + `head -c N` on infinite streams = silent SIGPIPE abort. Use `openssl rand` for random bytes instead.

## Next phase plan (Phase 4 — Databricks bronze ingestion)

1. Initialise Databricks workspace via UI (one-time): grant Azure user admin, configure access connector as external location credential.
2. Upload Synthea NDJSON (chosen 14 resources, ~15 GB) from local to `raw` container via `azcopy` or Databricks CLI.
3. Single-node Databricks cluster, Standard_DS3_v2 (4 vCPU / 14 GB), auto-terminate at 10 min, Photon disabled.
4. Bronze ingestion notebooks (one per resource type) in `databricks/notebooks/bronze/`:
   - Read NDJSON from `raw/` via the access connector's mounted ABFS path.
   - Write to bronze Delta tables in `bronze/` with schema-on-read + ingestion metadata (`load_ts`, `source_file`, `dw_row_hash`).
   - No business logic, no deduplication, no Pydantic validation — that's silver.
5. Databricks Asset Bundles to define jobs reproducibly (introduces databricks.yml).
6. Cost discipline: cluster auto-terminate aggressive, kill cluster manually between development sessions.

**Tier expectations**: ingestion notebooks = Tier B/C heavy (PySpark + Delta patterns are core learning). Asset bundle config = Tier A.

**Estimated cost**: $15–30 in Databricks compute across the phase. Will track per session.

## Cost tracker

| Phase | Item | Estimated | Actual |
|---|---|---|---|
| 1 | Dev tooling | $0 | $0 |
| 2 | Synthea + local storage | $0 | $0 |
| 3 | Azure infra creation | $0–5 | <$1 |
| 4 | Databricks compute + storage IOPS | $15–30 | TBD |
| 5–7 | Silver/gold Spark + dbt compute | $15–30 | TBD |
| 8 | OpenAI API (embeddings + RAG agent) | $5–15 | TBD |
| 9–11 | Power BI + CI minutes | $0–5 | TBD |
| **Total** | | **~$50** | TBD |
