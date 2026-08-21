"""End-to-end test of the silver validation path.

Unlike the unit tests, this exercises the real composition: registry lookup,
UDF factory, closure serialisation to executors, Delta writes, and the
reconciliation guard. Nothing is mocked.

This is also the only place the quarantine pattern is proven to work — the
Synthea dataset contains no invalid records, so real runs never exercise it.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from pyspark.sql import DataFrame, Row, SparkSession

from readmission_lakehouse.contracts.fhir import PatientContract
from readmission_lakehouse.silver.validate import validate_resource

# Fixture seeds 3 valid + 2 invalid Patient rows; assertions pin those counts.
_N_VALID = 3
_N_INVALID = 2
_N_SOURCE = _N_VALID + _N_INVALID

# Local OSS Delta + Spark 3.5 cannot overwrite via truncate; parquet is fine
# for these tests — they exercise validation/quarantine, not the storage format.
_TEST_FMT = "parquet"

_VALID_TABLE = "silver_patient_valid_test"
_QUARANTINE_TABLE = "silver_patient_quarantine_test"


@pytest.fixture
def bronze_patient(delta_spark: SparkSession) -> Iterator[str]:
    """Bronze-shaped Patient table: 3 valid records, 2 invalid.

    Invalid rows fail for different reasons so the test proves the contract
    catches more than one class of problem.
    """
    table = "bronze_patient_test"
    targets = (table, _VALID_TABLE, _QUARANTINE_TABLE)

    # Setup-time cleanup: a failed run never reaches teardown, so the metastore
    # can carry stale table names between runs even though the warehouse is fresh.
    for t in targets:
        delta_spark.sql(f"DROP TABLE IF EXISTS {t}")

    rows = [
        # --- valid ---
        Row(
            resourceType="Patient",
            id="p1",
            gender="male",
            birthDate="1980-01-01",
            deceasedBoolean=False,
            _load_ts="2026-01-01T00:00:00",
            _source_file="patients.ndjson",
            _row_hash="a" * 64,
            _ingestion_run_id="run-1",
        ),
        Row(
            resourceType="Patient",
            id="p2",
            gender="female",
            birthDate="1975-06-15",
            deceasedBoolean=False,
            _load_ts="2026-01-01T00:00:00",
            _source_file="patients.ndjson",
            _row_hash="b" * 64,
            _ingestion_run_id="run-1",
        ),
        Row(
            resourceType="Patient",
            id="p3",
            gender="other",
            birthDate="1990-12-31",
            deceasedBoolean=True,
            _load_ts="2026-01-01T00:00:00",
            _source_file="patients.ndjson",
            _row_hash="c" * 64,
            _ingestion_run_id="run-1",
        ),
        # --- invalid: gender outside the permitted set ---
        Row(
            resourceType="Patient",
            id="p4",
            gender="not-a-gender",
            birthDate="1985-03-03",
            deceasedBoolean=False,
            _load_ts="2026-01-01T00:00:00",
            _source_file="patients.ndjson",
            _row_hash="d" * 64,
            _ingestion_run_id="run-1",
        ),
        # --- invalid: birthDate unparseable as a date ---
        Row(
            resourceType="Patient",
            id="p5",
            gender="male",
            birthDate="not-a-date",
            deceasedBoolean=False,
            _load_ts="2026-01-01T00:00:00",
            _source_file="patients.ndjson",
            _row_hash="e" * 64,
            _ingestion_run_id="run-1",
        ),
    ]

    delta_spark.createDataFrame(rows).write.format(_TEST_FMT).saveAsTable(table)

    yield table

    for t in targets:
        delta_spark.sql(f"DROP TABLE IF EXISTS {t}")


def test_validation_splits_valid_and_invalid_records(
    delta_spark: SparkSession, bronze_patient: str
) -> None:
    result = validate_resource(
        spark=delta_spark,
        bronze_table=bronze_patient,
        valid_table=_VALID_TABLE,
        quarantine_table=_QUARANTINE_TABLE,
        fmt=_TEST_FMT,
        contract=PatientContract,
    )

    assert result["source_rows"] == _N_SOURCE
    assert result["valid_rows"] == _N_VALID
    assert result["quarantine_rows"] == _N_INVALID

    valid_ids = {r["id"] for r in delta_spark.table(_VALID_TABLE).collect()}
    assert valid_ids == {"p1", "p2", "p3"}

    quarantined = delta_spark.table(_QUARANTINE_TABLE).collect()
    assert {r["id"] for r in quarantined} == {"p4", "p5"}

    # Every quarantined row carries a diagnosable reason — the point of the pattern.
    for row in quarantined:
        assert row["_validation_error"]
        assert len(row["_validation_error"]) > 0


def test_valid_table_drops_the_error_column(delta_spark: SparkSession, bronze_patient: str) -> None:
    """Valid rows shouldn't carry an all-null error column downstream."""
    validate_resource(
        spark=delta_spark,
        bronze_table=bronze_patient,
        valid_table=_VALID_TABLE,
        quarantine_table=_QUARANTINE_TABLE,
        fmt=_TEST_FMT,
        contract=PatientContract,
    )
    assert "_validation_error" not in delta_spark.table(_VALID_TABLE).columns
    assert "_validation_error" in delta_spark.table(_QUARANTINE_TABLE).columns


def test_provenance_columns_survive_validation(
    delta_spark: SparkSession, bronze_patient: str
) -> None:
    """Bronze provenance must be preserved so a bad row can be traced back."""
    validate_resource(
        spark=delta_spark,
        bronze_table=bronze_patient,
        valid_table=_VALID_TABLE,
        quarantine_table=_QUARANTINE_TABLE,
        fmt=_TEST_FMT,
        contract=PatientContract,
    )
    for table in (_VALID_TABLE, _QUARANTINE_TABLE):
        cols = delta_spark.table(table).columns
        for c in ("_load_ts", "_source_file", "_row_hash", "_ingestion_run_id"):
            assert c in cols, f"{c} missing from {table}"


def test_reconciliation_guard_raises_on_row_loss(
    delta_spark: SparkSession,
    bronze_patient: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Force a mismatch and confirm the guard fires.

    Without this the guard is untested — real runs always reconcile cleanly.
    """
    real_table = delta_spark.table

    def lying_table(name: str) -> DataFrame:
        df = real_table(name)
        return df.limit(1) if name == _VALID_TABLE else df

    monkeypatch.setattr(delta_spark, "table", lying_table)

    with pytest.raises(ValueError, match="reconciliation failed"):
        validate_resource(
            spark=delta_spark,
            bronze_table=bronze_patient,
            valid_table=_VALID_TABLE,
            quarantine_table=_QUARANTINE_TABLE,
            fmt=_TEST_FMT,
            contract=PatientContract,
        )
