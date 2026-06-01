"""Bronze→Silver validation via Pydantic contracts (quarantine pattern).

Each bronze table has an associated Pydantic contract from Phase 2. We
apply the contract to every row via a PySpark UDF, then split:
  - Rows that validate → silver.<table>_valid
  - Rows that fail validation → silver.<table>_quarantine (with error attached)

Downstream silver dbt models read from _valid, not from bronze, so they're
guaranteed to see contract-conformant data.
"""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ValidationError
from pyspark.sql import Row, SparkSession
from pyspark.sql.functions import col, struct, udf
from pyspark.sql.types import StringType

INGESTION_METADATA_COLUMNS = frozenset(
    {"_load_ts", "_source_file", "_row_hash", "_ingestion_run_id"}
)


class ValidationResult(TypedDict):
    bronze_table: str
    valid_table: str
    quarantine_table: str
    total_rows: int
    valid_rows: int
    quarantine_rows: int


def build_validation_udf(contract: type[BaseModel]):  # type: ignore[no-untyped-def]
    """Build a Spark UDF that validates a struct against the given Pydantic contract.

    Returns:
        A PySpark UDF returning string. None means valid; non-None is the
        validation error message.

    Notes:
        We build the UDF inside a factory function so the contract class is
        captured in closure. Spark serialises the closure to send to executors;
        Pydantic v2 model classes are picklable, so this works.
    """

    def _validate(row: Row) -> str | None:
        row_dict = row.asDict(recursive=True)
        try:
            contract.model_validate(row_dict)
            return None
        except ValidationError as e:
            return str(e)

    return udf(_validate, StringType())


def validate_resource(
    spark: SparkSession,
    bronze_table: str,
    valid_table: str,
    quarantine_table: str,
    contract: type[BaseModel],
) -> ValidationResult:
    """Validate all rows in bronze_table against contract; split into valid/quarantine.

    Args:
        spark: SparkSession.
        bronze_table: fully-qualified bronze table name.
        valid_table: fully-qualified target for valid rows.
        quarantine_table: fully-qualified target for invalid rows.
        contract: Pydantic model class.

    Returns:
        ValidationResult with row counts for logging.
    """

    df = spark.table(bronze_table)

    validate_udf = build_validation_udf(contract)

    original_cols = [c for c in df.columns if c not in INGESTION_METADATA_COLUMNS]

    df_with_err = df.withColumn("_validation_error", validate_udf(struct(*original_cols)))

    df_valid = df_with_err.filter(col("_validation_error").isNull()).drop("_validation_error")
    df_quarantine = df_with_err.filter(col("_validation_error").isNotNull())

    df_valid.write.format("delta").mode("overwrite").saveAsTable(valid_table)
    df_quarantine.write.format("delta").mode("overwrite").saveAsTable(quarantine_table)

    valid_count = spark.table(valid_table).count()
    quarantine_count = spark.table(quarantine_table).count()
    total = valid_count + quarantine_count
    return ValidationResult(
        bronze_table=bronze_table,
        valid_table=valid_table,
        quarantine_table=quarantine_table,
        total_rows=total,
        valid_rows=valid_count,
        quarantine_rows=quarantine_count,
    )
