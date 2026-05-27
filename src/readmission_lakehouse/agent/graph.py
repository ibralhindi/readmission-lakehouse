"""Care-manager agent: a LangGraph that assembles a patient's structured profile,
their clinical notes (RAG), and evidence-based guidelines (RAG), then drafts a
cited intervention brief for clinician review.

Flow:  fetch_profile -> retrieve_notes -> retrieve_guidelines -> generate_plan

Decision-SUPPORT only: it suggests, a human clinician decides. Synthetic data.
"""

from __future__ import annotations

from typing import Any, TypedDict, cast

from langchain_chroma import Chroma
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from readmission_lakehouse.agent.config import (
    CHAT_MODEL,
    CHROMA_DIR,
    EMBED_MODEL,
    GUIDELINES_COLLECTION,
    NOTES_COLLECTION,
    require_openai_key,
)
from readmission_lakehouse.agent.profile import get_patient_profile


class AgentState(TypedDict):
    """Flows through the graph; each node fills in its piece."""

    patient_id: str
    profile: dict
    notes: list[str]
    guidelines: list[dict]
    plan: str


class AgentInput(TypedDict):
    """Minimum input needed to start the graph."""

    patient_id: str


# --- helpers (provided) -------------------------------------------------------
def _embeddings() -> OpenAIEmbeddings:
    require_openai_key()
    return OpenAIEmbeddings(model=EMBED_MODEL)


def _store(collection: str) -> Chroma:
    return Chroma(
        collection_name=collection,
        embedding_function=_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )


def _llm() -> ChatOpenAI:
    # Low temperature: this is clinical content, we want consistency over flair.
    return ChatOpenAI(model=CHAT_MODEL, temperature=0.2)


def _build_prompt(state: AgentState) -> list[BaseMessage]:
    """The prompt carries the safety framing — keep it as written."""
    profile_lines = "\n".join(f"  {k}: {v}" for k, v in state["profile"].items())
    notes_block = "\n\n".join(f"[note {i + 1}] {n}" for i, n in enumerate(state["notes"]))
    guidelines_block = "\n\n".join(f"[{g['title']}] {g['text']}" for g in state["guidelines"])

    system = SystemMessage(
        content=(
            "You are a clinical decision-SUPPORT assistant for a hospital care manager. "
            "You do not diagnose, prescribe, or make decisions — you summarize a patient's "
            "readmission-relevant picture and SUGGEST evidence-based interventions for a "
            "human clinician to review and act on. Be specific to this patient and never "
            "invent facts the notes don't support."
        )
    )
    human = HumanMessage(
        content=(
            f"PATIENT PROFILE (structured, from the data warehouse):\n{profile_lines}\n\n"
            f"RELEVANT EXCERPTS FROM THIS PATIENT'S CLINICAL NOTES:\n{notes_block}\n\n"
            f"CANDIDATE EVIDENCE-BASED INTERVENTIONS (cite the title when you use one):\n"
            f"{guidelines_block}\n\n"
            "Write a concise care-manager brief:\n"
            "1. A 2-3 sentence summary of this patient's readmission-relevant picture.\n"
            "2. 3-5 suggested interventions, each citing the guideline title it draws on.\n"
            "3. One line on what the clinician should verify or watch.\n"
            "Under ~250 words. Suggestions for clinician review, not directives."
        )
    )
    return [system, human]


def _message_content_to_text(content: str | list[str | dict[Any, Any]]) -> str:
    """Normalize LangChain message content blocks into plain text."""
    if isinstance(content, str):
        return content

    return "\n".join(
        part if isinstance(part, str) else str(part.get("text", part)) for part in content
    )


# --- nodes (YOU write the bodies) ---------------------------------------------
def fetch_profile(state: AgentState) -> AgentState:
    return {
        "patient_id": state["patient_id"],
        "profile": get_patient_profile(state["patient_id"]),
        "notes": [],
        "guidelines": [],
        "plan": "",
    }


def retrieve_notes(state: AgentState) -> AgentState:
    query = "diagnoses, medications, discharge, follow-up needs, risk factors"
    docs = _store(NOTES_COLLECTION).similarity_search(
        query, k=8, filter={"patient_id": state["patient_id"]}
    )
    return {**state, "notes": [d.page_content for d in docs]}


def retrieve_guidelines(state: AgentState) -> AgentState:
    query = " ".join(state["notes"][:3]) or "post-discharge readmission prevention"
    docs = _store(GUIDELINES_COLLECTION).similarity_search(query, k=4)
    return {
        **state,
        "guidelines": [{"title": d.metadata["title"], "text": d.page_content} for d in docs],
    }


def generate_plan(state: AgentState) -> AgentState:
    resp = _llm().invoke(_build_prompt(state))
    return {**state, "plan": _message_content_to_text(resp.content)}


# --- graph assembly (provided) ------------------------------------------------
def build_agent() -> CompiledStateGraph[AgentState, None, AgentInput, AgentState]:
    g: StateGraph[AgentState, None, AgentInput, AgentState] = StateGraph(
        AgentState, input_schema=AgentInput
    )
    g.add_node("fetch_profile", fetch_profile)
    g.add_node("retrieve_notes", retrieve_notes)
    g.add_node("retrieve_guidelines", retrieve_guidelines)
    g.add_node("generate_plan", generate_plan)

    g.add_edge(START, "fetch_profile")
    g.add_edge("fetch_profile", "retrieve_notes")
    g.add_edge("retrieve_notes", "retrieve_guidelines")
    g.add_edge("retrieve_guidelines", "generate_plan")
    g.add_edge("generate_plan", END)
    return g.compile()


agent = build_agent()


def run_agent(patient_id: str) -> AgentState:
    return cast(AgentState, agent.invoke({"patient_id": patient_id}))


if __name__ == "__main__":
    import sys

    from readmission_lakehouse.agent.profile import list_cohort_patients

    pid = sys.argv[1] if len(sys.argv) > 1 else list_cohort_patients(1)[0]["patient_id"]
    result = run_agent(pid)
    print(f"=== Care-manager brief for {pid} ===\n")
    print(result["plan"])
