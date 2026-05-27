"""Streamlit UI for the care-manager agent.

Run from the project root:
    uv run streamlit run src/readmission_lakehouse/agent/app.py
"""

from __future__ import annotations

import streamlit as st

from readmission_lakehouse.agent.graph import AgentState, run_agent
from readmission_lakehouse.agent.profile import list_cohort_patients

st.set_page_config(page_title="Readmission Care-Manager Assistant", page_icon="🏥", layout="wide")


@st.cache_data(show_spinner=False)
def _cohort() -> list[dict]:
    """Cached so the warehouse roster query runs once per session."""
    return list_cohort_patients()


@st.cache_data(show_spinner=False)
def _brief(patient_id: str) -> AgentState:
    """Cached per patient so re-viewing the same patient doesn't re-bill the LLM."""
    return run_agent(patient_id)


st.title("Readmission Care-Manager Assistant")
st.caption(
    "Clinical decision **support** — suggestions for a clinician to review, not "
    "directives. Built on synthetic Synthea data; no real patient information."
)

patients = _cohort()
labels = {
    f"{p['patient_id'][:8]}…  ·  {p['gender']}, {int(p['age'])}y  ·  "
    f"{'⚠ readmitted' if p['ever_readmitted'] else 'not readmitted'}": p["patient_id"]
    for p in patients
}
choice = st.selectbox(f"Select a patient  ({len(patients)} in cohort)", list(labels))
patient_id = labels[choice]

if st.button("Generate care brief", type="primary"):
    with st.spinner("Assembling profile, notes, and guidelines, then drafting the brief…"):
        st.session_state["result"] = _brief(patient_id)
        st.session_state["result_pid"] = patient_id

# Show the brief only while the selected patient matches the last one generated,
# so switching patients hides the stale brief until you regenerate.
if st.session_state.get("result_pid") == patient_id:
    result = st.session_state["result"]
    profile = result["profile"]

    st.subheader("Patient profile")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Age at admission", profile.get("age_at_admission", "—"))
    c2.metric("Length of stay (days)", profile.get("length_of_stay_days", "—"))
    c3.metric("Readmitted ≤30d", "Yes" if profile.get("was_readmitted_30d") else "No")
    c4.metric("Likely transfer", "Yes" if profile.get("is_likely_transfer") else "No")
    st.caption(
        f"{profile.get('gender', '?')} · {profile.get('race_display', '?')} · "
        f"{profile.get('ethnicity_display', '?')} · index admission "
        f"{profile.get('index_admission_date', '?')}"
    )

    st.subheader("Suggested care brief")
    st.markdown(result["plan"])

    with st.expander(f"Clinical notes used ({len(result['notes'])})"):
        for i, note in enumerate(result["notes"], 1):
            st.text(f"[note {i}]\n{note}")

    with st.expander(f"Guidelines referenced ({len(result['guidelines'])})"):
        for g in result["guidelines"]:
            st.markdown(f"**{g['title']}** — {g['text']}")
