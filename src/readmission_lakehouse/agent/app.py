"""Streamlit UI for the agentic care-manager assistant.

Run from the project root:
    uv run streamlit run src/readmission_lakehouse/agent/app.py
"""

from __future__ import annotations

import streamlit as st

from readmission_lakehouse.agent.graph import run_agent
from readmission_lakehouse.agent.profile import get_patient_profile, list_cohort_patients

st.set_page_config(page_title="Readmission Care-Manager Assistant", page_icon="🏥", layout="wide")


@st.cache_data(show_spinner=False)
def _cohort() -> list[dict]:
    return list_cohort_patients()


@st.cache_data(show_spinner=False)
def _profile(patient_id: str) -> dict:
    return get_patient_profile(patient_id)


@st.cache_data(show_spinner=False)
def _brief(patient_id: str) -> dict:
    return run_agent(patient_id)


st.title("Readmission Care-Manager Assistant")
st.caption(
    "Agentic clinical decision **support** — an LLM selects its own retrieval "
    "steps to assemble evidence, then suggests interventions for a clinician to "
    "review. Synthetic Synthea data; no real patient information."
)

patients = _cohort()
labels = {
    f"{p['patient_id'][:8]}…  ·  {p['gender']}, {int(p['age'])}y  ·  "
    f"{'⚠ readmission history' if p['ever_readmitted'] else 'no prior readmission'}": p[
        "patient_id"
    ]
    for p in patients
}
choice = st.selectbox(f"Select a patient  ({len(patients)} in cohort)", list(labels))
patient_id = labels[choice]

if st.button("Generate care brief", type="primary"):
    with st.spinner("The agent is gathering evidence and drafting the brief…"):
        st.session_state["result"] = _brief(patient_id)
        st.session_state["result_pid"] = patient_id

if st.session_state.get("result_pid") == patient_id:
    result = st.session_state["result"]
    profile = _profile(patient_id)

    st.subheader("Patient profile")
    c1, c2, c3 = st.columns(3)
    c1.metric("Age at admission", profile.get("age_at_admission", "—"))
    c2.metric("Length of stay (days)", profile.get("length_of_stay_days", "—"))
    c3.metric("Prior 30-day readmission", "Yes" if profile.get("ever_readmitted_30d") else "No")
    st.caption(
        f"{profile.get('gender', '?')} · {profile.get('race_display', '?')} · "
        f"{profile.get('ethnicity_display', '?')} · index admission "
        f"{profile.get('index_admission_date', '?')}"
    )

    st.subheader("Suggested care brief")
    st.markdown(result["plan"])

    with st.expander(f"How the agent worked — {len(result['steps'])} tool calls"):
        for i, step in enumerate(result["steps"], 1):
            query = step["args"].get("query")
            header = f"**{i}. `{step['tool']}`**" + (f" — query: *{query}*" if query else "")
            st.markdown(header)
            st.text(step["result"][:800])
