"""Agentic care-manager assistant (LangGraph tool-calling agent).

The LLM is given tools and a goal; it decides which to call, formulates its own
search queries, may retrieve again if a pass is thin, and decides when it has
enough evidence to write a cited decision-support brief. Control flow is
model-directed — this is an agent, not a fixed pipeline.

Decision-SUPPORT only: it suggests, a human clinician decides. Synthetic data.
"""

from __future__ import annotations

from typing import Any

from langchain_chroma import Chroma
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from readmission_lakehouse.agent.config import (
    CHAT_MODEL,
    CHROMA_DIR,
    EMBED_MODEL,
    GUIDELINES_COLLECTION,
    NOTES_COLLECTION,
    require_openai_key,
)
from readmission_lakehouse.agent.profile import get_patient_profile

SYSTEM_PROMPT = (
    "You are a clinical decision-SUPPORT assistant for a hospital care manager. "
    "Your goal: produce a concise, evidence-based intervention brief for the "
    "patient under review, for a human clinician to review — you suggest, you do "
    "not decide, diagnose, or prescribe.\n\n"
    "You have tools to (a) fetch the patient's structured profile, (b) search the "
    "patient's clinical notes, and (c) search a library of evidence-based "
    "interventions. Gather what you need — typically the profile first, then the "
    "notes, then guidelines relevant to what the notes reveal; search again if a "
    "pass is thin. When you have enough, write the brief WITHOUT calling more tools:\n"
    "1. A 2-3 sentence summary of the patient's readmission-relevant picture.\n"
    "2. 3-5 suggested interventions, each citing the guideline title it draws on.\n"
    "3. One line on what the clinician should verify.\n"
    "Under ~250 words. Be specific to this patient; never invent facts the notes "
    "don't support."
)

type AgentGraph = CompiledStateGraph[MessagesState, None, MessagesState, MessagesState]


# --- helpers ------------------------------------------------------------------
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
    require_openai_key()  # exports OPENAI_API_KEY (from Key Vault) before the client reads it
    # Low temperature: clinical content, consistency over flair.
    return ChatOpenAI(model=CHAT_MODEL, temperature=0.2)


def _message_content_to_text(content: str | list[str | dict[Any, Any]]) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(
        part if isinstance(part, str) else str(part.get("text", part)) for part in content
    )


# --- tools (bound to one patient per run; the model picks + queries them) -----
def _build_tools(patient_id: str) -> list:
    @tool
    def get_patient_profile_tool() -> str:
        """Structured profile for the patient under review: demographics, latest
        inpatient admission, length of stay, prior 30-day readmission history.
        Call this first."""
        profile = get_patient_profile(patient_id)
        if not profile:
            return "No structured profile found."
        return "\n".join(f"{k}: {v}" for k, v in profile.items())

    @tool
    def search_patient_notes(query: str) -> str:
        """Search THIS patient's clinical notes for the most relevant excerpts.
        Pass a query describing what you want (e.g. 'diagnoses, medications,
        social history, discharge plan')."""
        docs = _store(NOTES_COLLECTION).similarity_search(
            query, k=8, filter={"patient_id": patient_id}
        )
        if not docs:
            return "No notes found for this patient."
        return "\n\n".join(f"[note {i + 1}] {d.page_content}" for i, d in enumerate(docs))

    @tool
    def search_guidelines(query: str) -> str:
        """Search evidence-based readmission-reduction interventions. Pass a query
        describing the patient's clinical/social picture; returns guidelines with
        titles to cite in the brief."""
        docs = _store(GUIDELINES_COLLECTION).similarity_search(query, k=4)
        return "\n\n".join(f"[{d.metadata['title']}] {d.page_content}" for d in docs)

    return [get_patient_profile_tool, search_patient_notes, search_guidelines]


# --- the agent loop -----------------------------------------------------------
def _build_agent(patient_id: str) -> AgentGraph:
    tools = _build_tools(patient_id)
    llm_with_tools = _llm().bind_tools(tools)

    def agent_node(state: MessagesState) -> dict:
        # The model sees the running conversation and either emits tool calls
        # or writes the final brief. tools_condition decides which.
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    g: StateGraph[MessagesState, None, MessagesState, MessagesState] = StateGraph(MessagesState)
    g.add_node("agent", agent_node)
    g.add_node("tools", ToolNode(tools))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)  # -> "tools" or END
    g.add_edge("tools", "agent")
    return g.compile()


def _extract_steps(messages: list[BaseMessage]) -> list[dict]:
    """Pair each tool call with its result, for a visible reasoning trace."""
    results = {m.tool_call_id: m.content for m in messages if isinstance(m, ToolMessage)}
    steps = []
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                tool_call_id = tc.get("id") or ""
                steps.append(
                    {
                        "tool": tc["name"],
                        "args": tc.get("args", {}),
                        "result": _message_content_to_text(results.get(tool_call_id, "")),
                    }
                )
    return steps


def run_agent(patient_id: str) -> dict[str, Any]:
    app = _build_agent(patient_id)
    initial: list[AnyMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="Produce the care-manager brief for the patient under review."),
    ]
    # recursion_limit caps the agent loop — a cost/safety guard against runaway
    # tool-calling (the agent should finish in well under this).
    initial_state: MessagesState = {"messages": initial}
    config: RunnableConfig = {"recursion_limit": 12}
    final = app.invoke(initial_state, config)
    messages = final["messages"]
    return {
        "plan": _message_content_to_text(messages[-1].content),
        "steps": _extract_steps(messages),
    }


if __name__ == "__main__":
    import sys

    from readmission_lakehouse.agent.profile import list_cohort_patients

    pid = sys.argv[1] if len(sys.argv) > 1 else list_cohort_patients(1)[0]["patient_id"]
    result = run_agent(pid)
    print(f"=== Care-manager brief for {pid} ===\n{result['plan']}\n")
    print("--- Agent's tool calls (its decisions) ---")
    for s in result["steps"]:
        q = s["args"].get("query", "")
        print(f"  {s['tool']}" + (f"(query='{q}')" if q else "()"))
