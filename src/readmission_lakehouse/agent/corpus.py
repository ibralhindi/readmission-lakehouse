"""Build the Chroma corpus: patient clinical notes + intervention guidelines.

Notes: pull a sample of IMP-cohort patients' DocumentReference notes from
Databricks (base64-decoded), embed one note = one document into 'patient_notes',
keyed by note id so re-runs are idempotent. Guidelines: embed the curated set
into 'guidelines'.

Run: uv run python -m readmission_lakehouse.agent.corpus
"""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from readmission_lakehouse.agent import db
from readmission_lakehouse.agent.config import (
    CHROMA_DIR,
    EMBED_MODEL,
    GUIDELINES_COLLECTION,
    NOTES_COLLECTION,
    require_openai_key,
)
from readmission_lakehouse.agent.guidelines import GUIDELINES


def _notes_sql(n_patients: int) -> str:
    # n_patients is an int we control (not user input), so f-string is safe.
    # The regex grabs the trailing segment after the last '/' or ':', which is
    # the patient UUID regardless of "Patient/<uuid>" vs "urn:uuid:<uuid>".
    return f"""
        WITH cohort AS (
            SELECT DISTINCT dp.patient_id
            FROM rl_dev.gold.fact_readmission fr
            JOIN rl_dev.gold.dim_patient dp ON fr.patient_key = dp.patient_key
            ORDER BY dp.patient_id
            LIMIT {int(n_patients)}
        )
        SELECT
            dr.id                                              AS note_id,
            regexp_extract(dr.subject.reference, '([^/:]+)$', 1) AS patient_id,
            CAST(dr.date AS STRING)                            AS note_date,
            CAST(unbase64(dr.content[0].attachment.data) AS STRING) AS note_text
        FROM rl_dev.bronze.document_reference dr
        WHERE regexp_extract(dr.subject.reference, '([^/:]+)$', 1)
              IN (SELECT patient_id FROM cohort)
    """


def _store(collection: str) -> Chroma:
    require_openai_key()
    return Chroma(
        collection_name=collection,
        embedding_function=OpenAIEmbeddings(model=EMBED_MODEL),
        persist_directory=str(CHROMA_DIR),
    )


def _add_in_batches(
    store: Chroma,
    texts: list[str],
    metadatas: list[dict[str, str]],
    ids: list[str],
    batch_size: int = 5000,
) -> None:
    """Chroma's local backend caps a single add() at ~5461 docs; chunk under it."""
    for i in range(0, len(texts), batch_size):
        store.add_texts(
            texts=texts[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
            ids=ids[i : i + batch_size],
        )


def build_patient_notes(n_patients: int = 150) -> int:
    rows = [r for r in db.query(_notes_sql(n_patients)) if r["note_text"]]
    if not rows:
        raise RuntimeError(
            "No notes returned. The subject.reference probably doesn't end in the "
            "patient UUID — inspect `SELECT subject.reference FROM "
            "rl_dev.bronze.document_reference LIMIT 1` and adjust the regex."
        )
    _add_in_batches(
        _store(NOTES_COLLECTION),
        texts=[r["note_text"] for r in rows],
        metadatas=[
            {"patient_id": r["patient_id"], "note_date": r["note_date"] or ""} for r in rows
        ],
        ids=[r["note_id"] for r in rows],  # note id => idempotent upsert on re-run
    )
    return len(rows)


def build_guidelines() -> int:
    _store(GUIDELINES_COLLECTION).add_texts(
        texts=[g["text"] for g in GUIDELINES],
        metadatas=[{"title": g["title"]} for g in GUIDELINES],
        ids=[g["id"] for g in GUIDELINES],
    )
    return len(GUIDELINES)


if __name__ == "__main__":
    n_notes = build_patient_notes()
    print(f"Embedded {n_notes} patient notes into '{NOTES_COLLECTION}'.")
    n_g = build_guidelines()
    print(f"Embedded {n_g} guideline docs into '{GUIDELINES_COLLECTION}'.")

    # Sanity check: a guideline query should retrieve relevant interventions.
    hits = _store(GUIDELINES_COLLECTION).similarity_search(
        "patient discharged with heart failure, what should the care team do", k=2
    )
    print("Top guideline matches:", [h.metadata["title"] for h in hits])
