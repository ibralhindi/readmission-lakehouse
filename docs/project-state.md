# Project State — End of Phase 8

Last updated: 2026-05-27. Phase 8 complete. Phases 1–8 of 11 done.

## Project Context

Hospital 30-day readmission risk lakehouse on Azure, with an agentic RAG
care-manager assistant on top. Cross-industry parallel = churn.
Owner: Ibrahim Al-Hindi (data scientist + CPA → data engineer).
Budget $500. Repo: github.com/ibralhindi/readmission-lakehouse (public).

## Tech Stack (locked)

Python 3.12 + uv + ruff + mypy. Synthea FHIR R4 NDJSON, 10k MA patients seed=42.
Azure australiaeast. Terraform 1.15 + azurerm 4.x + azuread 3.x + databricks 1.x.
Databricks Premium, DBR 17.3 LTS. PySpark 3.5 + delta-spark 3.2. dbt-databricks 1.12
(dbt-core 1.11) + dbt_utils. Apache Airflow 3.2.1 (local Docker, CeleryExecutor).
Agentic RAG: LangGraph (tool-calling) + langchain-openai + langchain-chroma +
Chroma (local) + databricks-sql-connector + streamlit + python-dotenv.
OpenAI text-embedding-3-small (embed), gpt-4o-mini (chat). Power BI (Phase 9).

## Working Agreements (unchanged)

Tier scaffolding A/B/C. End-of-phase snapshots + quizzes + decisions log.
WHY-not-WHAT comments. AI collaboration disclosed in README. No-hallucination
rule honored throughout Phase 8 (verified LangGraph tool-calling API and
databricks-sql-connector M2M auth via search; pulled exact gold columns from
the transcript rather than guess).

## Repo Structure (Phase 8 additions)

readmission-lakehouse/
├── databricks.yml                              # Asset Bundle root
├── resources/{bronze_ingestion,silver_validation}.yml
├── dbt/{dbt_project.yml, packages.yml, macros/, models/{silver,gold}/, snapshots/}
├── airflow/                                    # Phase 7
│   ├── Dockerfile, requirements.txt, docker-compose.yaml, .env, dbt-profiles/
│   └── dags/readmission_pipeline.py            # retries+backoff, timeouts, auto-pause
├── src/readmission_lakehouse/
│   ├── bronze/, silver/, contracts/, tools/    # Phases 4–5
│   └── agent/                                  # Phase 8
│       ├── init.py
│       ├── config.py          # loads .env; EMBED_MODEL, CHAT_MODEL, CHROMA_DIR
│       ├── db.py              # warehouse access via SP OAuth M2M
│       ├── guidelines.py      # 7 curated evidence-based interventions
│       ├── corpus.py          # build patient_notes + guidelines Chroma collections
│       ├── profile.py         # structured profile from gold + cohort list
│       ├── graph.py           # tool-calling LangGraph agent
│       └── app.py             # Streamlit care-manager UI
├── tests/unit/{bronze,silver}/
├── scripts/{setup-phase3-.sh, upload-synthea-to-adls.sh, smoke_rag.py}
├── docs/{data-dictionary,decisions,quiz-log,project-state}.md
├── .env                       # gitignored: OPENAI_API_KEY + DATABRICKS_ (SP M2M)
├── .chroma/                   # gitignored: local vector store
└── pyproject.toml             # rag dep group added

## Live Azure / Databricks Resources (unchanged from Phase 7)

RG rl-rg-dev | Storage rlst3e33 (ADLS Gen2) | Key Vault rl-kv-3e33 |
DBX workspace rl-dbx-3e33 (Premium) | Access Connector rl-ac-3e33 | CI app rl-gh-actions-dev (OIDC).
UC: catalog rl_dev | schemas bronze/silver/gold | external locations rl-{bronze,silver,gold,raw}-dev.
Cluster rl-dev-interactive (Dedicated, dev-only). SQL warehouse rl-dbt-warehouse
(Serverless, 2X-Small) — used by Airflow's dbt task AND the agent's profile/db queries.
Service principal rl-airflow-dev (OAuth M2M) — same machine identity for both
the pipeline and the agent.

## Phase 8 — Agentic RAG Care-Manager Assistant

### Corpus (in .chroma/)

- patient_notes: 12,619 clinical notes for the 150-patient IMP cohort, base64-
decoded from bronze.document_reference (one note = one doc, metadata
patient_id + note_date). Embedded via text-embedding-3-small (1,536-dim).
Note: Chroma local backend caps a single add() at 5,461 → embedded in
batches of 5,000 via _add_in_batches.
- guidelines: 7 curated original summaries of evidence-based readmission-
reduction interventions (med rec, timely follow-up, teach-back, transitional
care, post-discharge contact, SDOH, HF self-management).

### Cohort (locked for consistency)

- 150 patients: DISTINCT from fact_readmission JOIN dim_patient ORDER BY
patient_id LIMIT 150. The SAME query underlies both the corpus build and
list_cohort_patients() (UI roster), guaranteeing the UI only offers
patients we have notes for.

### Agent (tool-calling LangGraph) — agentic, not a workflow

- State: MessagesState (conversation history with add_messages reducer).
- Tools (closed over patient_id per run — no UUID-passing through the model):
  get_patient_profile_tool()  → structured profile from gold via warehouse
  search_patient_notes(query) → Chroma similarity_search filtered by patient_id, k=8
  search_guidelines(query)    → Chroma similarity_search over guidelines, k=4
- Graph: START → agent → (tools_condition) → tools → agent → … → END.
Model decides WHICH tools to call, WHAT queries to write, WHETHER to
retrieve again, and WHEN to stop and compose the brief.
- LLM: gpt-4o-mini, temperature 0.2.
- System prompt: decision-support framing, cite guideline titles, ≤250 words,
structured output (summary + 3-5 interventions + verify line).
- recursion_limit=12 caps the loop (cost/safety guard).
- run_agent() returns {plan, steps} — the brief + the tool-call trace parsed
from messages (AIMessage.tool_calls paired with ToolMessage results).

### UI (Streamlit)

- Patient picker labelled "… · ,y · ⚠ readmission
history | no prior readmission".
- Generate button (button-gated + @st.cache_data + session_state — re-viewing
the same patient is free; the brief persists across UI reruns).
- Profile metrics (Age at admission, LOS days, Prior 30-day readmission —
patient-level, transfer-excluded for consistency with the picker).
- Brief + a "How the agent worked" expander showing the tool-call trace —
the agentic behavior made visible to the viewer.

### Auth

- Service principal rl-airflow-dev (the Airflow SP) reused. databricks-sql-
connector with credentials_provider + oauth_service_principal from
databricks.sdk.core. OpenAI key + DATABRICKS_* live in gitignored .env.
- Deferred to Phase 10: move all secrets to Key Vault (Airflow KV secrets
backend, app pulls OPENAI_API_KEY from KV).

### Bugs caught + fixed in Phase 8

- Chroma 5,461 add-cap → _add_in_batches.
- Picker/profile metric inconsistency — two correct queries telling different
stories. Root cause: GRAIN mismatch (patient-level "ever" vs admission-level
"latest") compounded by MEASURE mismatch (transfer-excluded vs raw).
Aligned both on patient-level transfer-excluded "Prior 30-day readmission"
— also the more clinically meaningful signal (prior readmission predicts
the next).

### Phase 8 narrative arc

Built it first as a *workflow* — linear LangGraph pipeline (fetch_profile →
retrieve_notes → retrieve_guidelines → generate_plan), each node hand-wired,
LLM only generated. Then converted to a true *agent* — bound the retrieval
functions as tools, let the model select+sequence them and write its own
queries. Verified agentic behavior in the trace: the model's third tool call
used terms (homelessness, IPV, social isolation) that came from the second
call's results, demonstrating model-directed adaptive retrieval.

## Phase Status

- [COMPLETED] 1 Scaffold | 2 Contracts | 3 Infra | 4 Bronze | 5 Silver
        | 6 Gold | 7 Airflow | 8 Agentic RAG
- [PENDING]   9 Power BI | 10 CI/dbt + Key Vault hardening | 11 README

## Cost Tracker


| Phase                                          | Spend            |
| ---------------------------------------------- | ---------------- |
| 1–6                                            | ~$13             |
| 7 (Airflow + end-to-end + warehouse + retries) | ~$8              |
| 8 (OpenAI embeddings + agent runs + warehouse) | ~$1              |
| **Total**                                      | **~$22 of $500** |


OpenAI: corpus embedding ~$0.20, agent runs <$0.001 each. Serverless warehouse
usage: cents. The ~$22 still includes the silent ~$1/day standing workspace
networking (NAT gateway / public IP in the Databricks managed RG) — DBUs are
only part of the bill.

## Key Interview Talking Points (Phase 8 additions)

**RAG mechanics**: an embedding model maps text to a ~1,500-dim vector
positioned so similar meanings sit near each other. The query is embedded with
the SAME model; the store returns nearest neighbors by cosine similarity.
That's why "heart failure readmission" matches "congestive heart failure
discharge" with zero shared keywords — it's meaning-space, not lexical search.

**Two collections, same mechanism, different inputs**: patient_notes uses a
clinical probe query *filtered by patient_id* (narrow to one patient, then
rank). guidelines uses the patient's top retrieved notes AS the query — the
patient's clinical reality selects the relevant interventions.

**Workflow vs agent — the line crossed in 8.4b**: the linear pipeline was a
workflow (developer-defined control flow). The tool-calling agent inverts it:
the LLM is bound to tools and directs its own process — selecting tools,
writing its own queries, looping, and deciding when done. Concrete proof from
a real run: after the second tool call (notes) surfaced homelessness/IPV/
isolation, the model's third tool call query was
`search_guidelines(query='homelessness, intimate partner abuse, social isolation, …')` — content from a prior tool result shaping the next tool call.

**Why RAG closes the business loop**: the gold star schema gives the
readmission RATE (13.64%, transfer-excluded). RAG over notes surfaces WHY
this patient is at risk (social determinants, never in the structured
warehouse) and WHAT to do (cited interventions). Structured tells the rate;
unstructured tells the story.

**Decision-support safety**: system prompt frames "suggest, don't decide";
cites guideline titles; UI shows the agent's tool-call trace so a clinician
sees what it drew on; README + caption disclose synthetic data + clinician-
review intent. Deliberately not "autonomous clinical AI."

**Chroma + embedding choices**: local Chroma + text-embedding-3-small is right
for a portfolio (free, simple); production swaps to a managed vector store
(Databricks Vector Search / Pinecone) for governance + multi-tenant scaling,
embedding model unchanged unless evaluation justifies a domain-tuned model.

**Metric grain consistency**: the picker/profile mismatch — two correct
queries told two stories because grains (patient vs latest admission) and
measures (transfer-excluded vs raw) differed. Lesson: every metric needs a
defined grain and a single source measure, or your dashboard contradicts
itself and erodes user trust.

**Service-principal reuse**: same SP runs the Airflow pipeline and the local
agent's warehouse queries (databricks-sql-connector + oauth_service_principal).
One machine identity, two consumers — clean separation of human dev auth
(your OAuth U2M) from automated auth.

**Chroma batch cap**: local Chroma caps a single add() at ~5,461 docs (SQLite
limit). Real-world quirk worth knowing; chunk writes under the cap.
