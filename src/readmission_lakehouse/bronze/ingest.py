"""Bronze ingestion: read FHIR NDJSON, add provenance, write Delta.

The bronze layer is intentionally minimal — schema-on-read, no business logic,
no deduplication. We only add four metadata columns so silver can answer
"where did this row come from and when did we see it last".
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypedDict

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    current_timestamp,
    input_file_name,
    lit,
    sha2,
    struct,
    to_json,
)


class IngestResult(TypedDict):
    """Return shape of ingest_resource — small enough to inline a TypedDict."""

    target_table: str
    source_path: str
    ingestion_run_id: str
    row_count: int


def add_ingestion_metadata(df: DataFrame, ingestion_run_id: str) -> DataFrame:
    """Add four provenance columns to a dataframe ahead of bronze write.

    Args:
        df: input dataframe (any schema). Treated as immutable.
        ingestion_run_id: unique label for this ingestion run.

    Returns:
        New dataframe with original columns plus _load_ts, _source_file,
        _row_hash, _ingestion_run_id.

    Notes:
        _row_hash is computed BEFORE the metadata cols are added so that the
        hash depends only on source data — unchanged source rows produce
        identical hashes across runs, enabling MERGE-based deduplication later.
    """
    # 1. Capture df.columns into a local variable BEFORE adding any metadata
    #    columns. The hash function below uses this exact list, and you can't
    #    compute it from `df.columns` later because by then metadata cols exist.
    original_columns = df.columns
    #
    # 2. Add the metadata columns.
    df_with_meta = df.withColumn("_load_ts", current_timestamp())
    df_with_meta = df_with_meta.withColumn("_source_file", input_file_name())

    #  Three nested functions: pack original cols into a struct, serialise
    #  that struct to a JSON string, take SHA-256 (256-bit) hex.
    #  The `256` arg is the digest length in bits; sha2 also supports 384/512.
    df_with_meta = df_with_meta.withColumn(
        "_row_hash", sha2(to_json(struct(*original_columns)), 256)
    )
    df_with_meta = df_with_meta.withColumn("_ingestion_run_id", lit(ingestion_run_id))

    return df_with_meta  # noqa: RET504


def ingest_resource(
    spark: SparkSession,
    source_path: str,
    target_table: str,
    ingestion_run_id: str | None = None,
) -> IngestResult:
    """Ingest one FHIR resource type from NDJSON to a bronze Delta table.

    Args:
        spark: active SparkSession.
        source_path: ADLS Gen2 URI to NDJSON file or glob, e.g.
            abfss://raw@rlst3e33.dfs.core.windows.net/synthea/Patient.ndjson.gz
        target_table: fully qualified bronze table name, e.g.
            rl_dev.bronze.patient
        ingestion_run_id: optional override. If None, auto-generates a UTC
            timestamp-based ID.

    Returns:
        IngestResult dict for logging.
    """
    # TODO(you):
    # 1. If ingestion_run_id is None, generate one.
    if ingestion_run_id is None:
        ingestion_run_id = f"bronze_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    #
    # 2. Read NDJSON:
    #    Spark handles .gz transparently — no need to mention compression.
    df_raw = spark.read.json(source_path)
    #
    # 3. Apply metadata:
    df_with_meta = add_ingestion_metadata(df_raw, ingestion_run_id)
    #
    # 4. Write Delta in overwrite mode (the snapshot-ingest pattern):
    df_with_meta.write.format("delta").mode("overwrite").save(target_table)
    #
    #    overwrite semantics: replaces all data; if the table doesn't exist,
    #    creates it. Idempotent: re-running the same source gives identical
    #    target state. Schema-on-read: Spark infers the schema from NDJSON and
    #    writes it into Delta's schema metadata on first write; subsequent
    #    overwrites with incompatible schemas would fail (we'd add
    #    .option("overwriteSchema", "true") if intentional).
    #
    # 5. Read back the row count for the return value:
    row_count = df_with_meta.count()
    #
    # 6. Return an IngestResult dict.
    return IngestResult(
        target_table=target_table,
        source_path=source_path,
        ingestion_run_id=ingestion_run_id,
        row_count=row_count,
    )
