"""End-to-end smoke test: embed one string via OpenAI, store + retrieve in Chroma.

Confirms the key works and the embed->store->retrieve path is wired before we
build the real corpus. Run: uv run python scripts/smoke_rag.py
"""

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from readmission_lakehouse.agent.config import CHROMA_DIR, EMBED_MODEL, require_openai_key

require_openai_key()  # fail fast with a clear message if missing

embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
store = Chroma(
    collection_name="smoke",
    embedding_function=embeddings,
    persist_directory=str(CHROMA_DIR),
)

store.add_texts(["Patient with congestive heart failure, readmitted within 30 days of discharge."])

hits = store.similarity_search("heart failure readmission", k=1)
print("Retrieved:", hits[0].page_content)
print("Smoke test passed — OpenAI embeddings + Chroma round-trip works.")
