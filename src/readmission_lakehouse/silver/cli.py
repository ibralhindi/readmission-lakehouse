"""CLI entrypoint for silver validation."""

from __future__ import annotations

import argparse
import logging

from pyspark.sql import SparkSession

from readmission_lakehouse.silver.resources import SILVER_VALIDATIONS
from readmission_lakehouse.silver.validate import validate_resource

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Validate one bronze resource against its Pydantic contract.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--resource-name",
        required=True,
        choices=[v.name for v in SILVER_VALIDATIONS],
        help="FHIR resource type to validate.",
    )
    args = parser.parse_args()

    validation = next(v for v in SILVER_VALIDATIONS if v.name == args.resource_name)

    spark = SparkSession.builder.getOrCreate()

    logger.info(
        f"Validating {validation.name}: "
        f"{validation.bronze_table} -> {validation.valid_table} | {validation.quarantine_table}"
    )
    result = validate_resource(
        spark=spark,
        bronze_table=validation.bronze_table,
        valid_table=validation.valid_table,
        quarantine_table=validation.quarantine_table,
        contract=validation.contract,
    )
    logger.info(
        f"Validated {result['total_rows']:,} rows: "
        f"{result['valid_rows']:,} valid, "
        f"{result['quarantine_rows']:,} quarantined."
    )
