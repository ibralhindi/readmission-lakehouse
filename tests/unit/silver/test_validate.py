"""Tests for silver validation logic — the SPEC for validate_resource.

Implement src/readmission_lakehouse/silver/validate.py until these pass.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from pyspark.sql import SparkSession
from pyspark.sql.functions import struct

from readmission_lakehouse.silver.validate import build_validation_udf


class _ToyContract(BaseModel):
    """Tiny Pydantic model for testing. Mirrors the shape of our FHIR contracts:
    a required id, an optional gender, extra fields ignored."""

    id: str
    gender: str | None = Field(default=None)

    model_config = {"extra": "ignore"}


def test_udf_returns_null_for_valid_row(spark: SparkSession) -> None:
    df = spark.createDataFrame([{"id": "p1", "gender": "male", "extra_field": "ignored"}])
    udf_fn = build_validation_udf(_ToyContract)

    result = df.withColumn("_err", udf_fn(struct(*df.columns)))
    error = result.collect()[0]["_err"]
    assert error is None


def test_udf_returns_string_for_invalid_row(spark: SparkSession) -> None:
    # _ToyContract requires `id` — omit it to force a validation error
    df = spark.createDataFrame([{"gender": "male"}])
    udf_fn = build_validation_udf(_ToyContract)

    result = df.withColumn("_err", udf_fn(struct(*df.columns)))
    error = result.collect()[0]["_err"]
    assert error is not None
    assert "id" in error  # Pydantic's error message mentions the missing field


def test_udf_handles_mixed_valid_and_invalid(spark: SparkSession) -> None:
    df = spark.createDataFrame(
        [
            {"id": "p1", "gender": "male"},  # valid
            {"id": None, "gender": "female"},  # invalid (id is None)
            {"id": "p3", "gender": "other"},  # valid
        ]
    )
    udf_fn = build_validation_udf(_ToyContract)

    result = df.withColumn("_err", udf_fn(struct(*df.columns))).collect()
    errors = [row["_err"] for row in result]
    assert errors[0] is None
    assert errors[1] is not None
    assert errors[2] is None
