"""Tests for bronze ingestion metadata logic.

These tests are the SPEC for add_ingestion_metadata.
Implement the function in src/readmission_lakehouse/bronze/ingest.py until all
tests pass.
"""

from __future__ import annotations

import pytest
from pyspark.sql import DataFrame, SparkSession

from readmission_lakehouse.bronze.ingest import add_ingestion_metadata

# SHA-256 hex digest is 256 bits → 64 lowercase hex characters.
_SHA256_HEX_LEN = 64


@pytest.fixture
def sample_df(spark: SparkSession) -> DataFrame:
    """Tiny three-row dataframe mirroring a FHIR Patient shape."""
    return spark.createDataFrame(
        [
            {"id": "p1", "gender": "male", "birthDate": "1980-01-01"},
            {"id": "p2", "gender": "female", "birthDate": "1985-05-15"},
            {"id": "p3", "gender": "other", "birthDate": "1990-12-31"},
        ]
    )


def test_adds_four_metadata_columns(sample_df: DataFrame) -> None:
    result = add_ingestion_metadata(sample_df, "test_run_001")
    for col in ["_load_ts", "_source_file", "_row_hash", "_ingestion_run_id"]:
        assert col in result.columns, f"Missing metadata column: {col}"


def test_preserves_original_columns(sample_df: DataFrame) -> None:
    result = add_ingestion_metadata(sample_df, "test_run_001")
    for col in sample_df.columns:
        assert col in result.columns, f"Original column missing: {col}"


def test_run_id_constant_across_rows(sample_df: DataFrame) -> None:
    result = add_ingestion_metadata(sample_df, "test_run_001")
    run_ids = {row["_ingestion_run_id"] for row in result.collect()}
    assert run_ids == {"test_run_001"}


def test_load_ts_constant_across_rows(sample_df: DataFrame) -> None:
    """All rows in one load share one load timestamp.

    This matters for downstream "show me all rows from load X" queries.
    """
    result = add_ingestion_metadata(sample_df, "test_run_001")
    load_timestamps = {row["_load_ts"] for row in result.collect()}
    assert len(load_timestamps) == 1


def test_row_hash_differs_for_different_rows(sample_df: DataFrame) -> None:
    result = add_ingestion_metadata(sample_df, "test_run_001")
    hashes = [row["_row_hash"] for row in result.collect()]
    assert len(set(hashes)) == len(hashes), "Row hashes should be unique"


def test_row_hash_excludes_metadata_columns(sample_df: DataFrame) -> None:
    """Hash is computed from original data only.

    Implication: re-running with a different run_id produces identical hashes
    for unchanged rows. This enables future MERGE-based incremental ingestion
    to detect unchanged rows and skip them.
    """
    result_a = add_ingestion_metadata(sample_df, "run_aaa")
    result_b = add_ingestion_metadata(sample_df, "run_bbb")
    hashes_a = sorted(row["_row_hash"] for row in result_a.collect())
    hashes_b = sorted(row["_row_hash"] for row in result_b.collect())
    assert hashes_a == hashes_b


def test_row_hash_is_sha256_hex(sample_df: DataFrame) -> None:
    result = add_ingestion_metadata(sample_df, "test_run_001")
    for row in result.collect():
        h = row["_row_hash"]
        assert len(h) == _SHA256_HEX_LEN, (
            f"Expected {_SHA256_HEX_LEN}-char SHA-256 hex, got {len(h)}: {h}"
        )
        assert all(c in "0123456789abcdef" for c in h)
