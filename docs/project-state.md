# Project State

> Updated at end of each phase. Combined with the original project brief, this doc plus the current chat is sufficient to resume work in a new session.

## Project identity

- **Name**: readmission-lakehouse
- **Goal**: Hospital readmission risk lakehouse on Azure — portfolio project for data scientist → data engineer transition (Melbourne, AU)
- **Business problem**: 30-day readmissions cost US$26B annually and are penalised under CMS HRRP / AU AIHW PPH frameworks. Build a unified platform that consolidates patient/encounter/condition data, computes readmission KPIs, identifies high-risk patients, and equips care managers with evidence-based interventions via RAG.
- **Cross-industry parallel**: readmission ≅ churn. Architecture is industry-agnostic.
- **Timeline**: 17–21 working days, 5–6 hrs/day. Hard ceiling 3 weeks.
- **Budget**: $500. Spent so far: $0.

## Status

- **Completed**: Phase 1 (scaffolding), Phase 2 (data + contracts)
- **Current**: Phase 3 — Terraform / Azure infrastructure
- **Repo**: https://github.com/ibralhindi/readmission-lakehouse (public)
- **Dev environment**: Windows 11 + WSL2 Ubuntu, Cursor IDE, Python 3.12, uv

## Tech stack (locked)

| Layer | Choice |
|---|---|
| Language | Python 3.12 (matches Databricks Runtime 17) |
| Package mgr | uv |
| Lint/format | ruff |
| Type check | mypy strict |
| Tests | pytest, ≥60% coverage gate |
| Pre-commit | ruff, mypy, trailing-whitespace, large-file guard |
| Source data | Synthea, FHIR R4 Bulk Export NDJSON, 10k MA patients, seed=42 |
| Cloud | Azure (ADLS Gen2, Key Vault, Azure Databricks) |
| IaC | Terraform |
| CI/CD | GitHub Actions (OIDC federation, no long-lived secrets) |
| Containers | Docker (Airflow stack) |
| Processing | Databricks + PySpark, Delta Lake, medallion (bronze/silver/gold) |
| Modelling | Kimball star, dbt with snapshots for SCD2 |
| Orchestration | Apache Airflow 3.x, local Docker, Databricks operator |
| BI | Power BI Desktop |
| LLM | OpenAI API direct (text-embedding-3-small + gpt-4o-mini) |
| Vector store | Databricks Vector Search (or Chroma fallback) |

## Repository layout (key paths)

```
readmission-lakehouse/
├── .cursor/rules/             # 5 rules: project, python, DE, behaviour, learning-mode
├── .vscode/                   # extensions.json + settings.json (committed)
├── .github/workflows/         # (empty; populated Phase 10)
├── airflow/                   # (empty; populated Phase 7)
├── databricks/                # (empty; populated Phases 4-5)
├── dbt/                       # (empty; populated Phase 6)
├── terraform/                 # (empty; populated Phase 3)
├── src/readmission_lakehouse/
│   ├── contracts/fhir.py      # Pydantic v2 models for 6 core FHIR resources
│   └── tools/
│       ├── profile_synthea.py # CLI: scans NDJSON, emits data dictionary
│       └── sample_synthea.py  # CLI: extracts 50-patient subset for CI
├── data/synthea/
│   ├── synthea.properties     # reproducibility config
│   └── output/                # 37G raw NDJSON (gitignored)
├── data/synthea_sample/       # 101M, 50 patients, committed
├── docs/
│   ├── data-dictionary.md     # 24 sections; 14 bronzed, 10 not
│   └── project-state.md       # this file
├── dashboards/                # Power BI (Phase 9)
├── Makefile                   # install, lint, format, test, clean, tree
└── pyproject.toml             # 3 dep groups: main, dev, rag
```

## Key decisions and rationale

1. **FHIR NDJSON over CSV**: matches HL7 Bulk Data Export spec; production-realistic; nested structure forces real Spark work.
2. **WSL2-first dev**: parity with Linux production runtimes; avoids Windows path/line-ending bugs.
3. **uv + ruff + mypy strict + Pydantic v2**: modern Python toolchain; portfolio signals competence to recruiters reading the repo.
4. **Hand-rolled slim contracts vs `fhir.resources` lib**: validates only what we use, doubles as documentation, demonstrates contract design.
5. **Bronze plan: 14 of 22 resources, ~15 GB**: ExplanationOfBenefit (9.9G), DiagnosticReport (2.8G), Provenance (952M), ImagingStudy, MedicationAdministration, SupplyDelivery, Device deferred — either redundant with bronzed resources or out of scope for readmission analytics.
6. **DocumentReference (2.1G) bronzed for RAG corpus**: Phase 8 will chunk + embed clinical narratives.
7. **SNOMED CT (not ICD-10)**: Synthea default; matches AU Digital Health Agency standard; defensible interview position.
8. **Hospitalization sub-resource sparse (~0.1%)**: readmission detection will key off `class.code IN ('IMP','EMER')` + `period`, not `hospitalization` sub-fields.
9. **Three-tier learning-mode scaffolding** (`.cursor/rules/40-learning-mode.mdc`): A=write fully, B=skeleton + TODOs, C=hints only. User writes core logic; Cursor handles boilerplate.

## Working agreements

- Every step gets a one-paragraph "why".
- Non-trivial files/commands/prompts get a breakdown.
- Cursor prompts state tier classification before generating.
- Project-state.md regenerated at end of each phase.

## Data inventory

- **Patients**: 11,423 (gender 50/50, deceased 11.8%, birth years 1910s–2020s)
- **Encounters**: 664,623 (status 100% finished, class predominantly AMB; ~0.8% IMP)
- **Conditions**: 412,692 (SNOMED CT; top codes are SDOH and minor clinical)
- **Sample for CI**: 50 patients, 101 MB, all 22 NDJSON files preserved

## Open issues / deferred decisions

- **OpenAI org**: API key not yet provisioned. Phase 8.
- **Azure subscription**: account exists, $0 credits — pay-as-you-go from Phase 3. Need to verify region availability for Databricks (target australiaeast).
- **Power BI Pro licence**: not needed for Desktop development; reassess if we want online publishing.
- **GitHub Actions OIDC vs PAT**: choose in Phase 3 (OIDC is the production-correct path; PAT is fallback if federation setup blocks).
- **Synthea geography**: currently Massachusetts; AU geography swap deferred unless time permits.

## Interview talking points (accumulated)

- "Chose FHIR Bulk Export format because that's what real EMRs send under 21st Century Cures Act compliance, not CSV."
- "Made an explicit bronze-scope decision — EOB at 9.9 GB would have tripled processing cost for redundant data."
- "Found a real bug in my own sampler: assumed `urn:uuid:` references, but Synthea exports use `Patient/<id>`. Caught it on the 660k-row Encounter file during integration."
- "Defaulted to SNOMED CT alignment because that's the AU Digital Health Agency standard; would add SNOMED→ICD-10 crosswalk for US workloads."
- "Derived readmission from `Encounter.class` + `period` because Synthea's `hospitalization` sub-resource is only populated on 0.1% of records — real-world data is sparser than tutorials suggest."

## Next phase plan (Phase 3 — Terraform → Azure)

Provision infra via Terraform:
- Resource group (`australiaeast`)
- Storage account, ADLS Gen2 with hierarchical namespace + containers `bronze`, `silver`, `gold`, `raw`
- Key Vault for secrets
- Databricks workspace (Standard tier)
- Service principal + RBAC for Databricks → ADLS access
- GitHub OIDC federation so CI can run `terraform plan/apply` without long-lived secrets
- Remote state backend (storage account container `tfstate`)

Tier expectations: Terraform modules = Tier B/C heavy; backend config + provider blocks = Tier A.

## Cost tracker

| Phase | Item | Estimated | Actual |
|---|---|---|---|
| 1 | Dev tooling | $0 | $0 |
| 2 | Synthea + storage | $0 | $0 |
| 3 | Azure infra (RG, ADLS, KV, DBX workspace creation) | $0–5 | TBD |
| 4–7 | Databricks compute, ADLS ops | $30–60 | TBD |
| 8 | OpenAI API (embeddings + RAG) | $5–15 | TBD |
| 9–11 | Power BI Pro (only if publishing), CI minutes | $0–10 | TBD |
| **Total** | | **~$50** | TBD |
