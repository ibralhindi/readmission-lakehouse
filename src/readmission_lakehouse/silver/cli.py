"""CLI entrypoint for silver validation."""

from __future__ import annotations

import argparse
import logging
import sys

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
    parser.add_argument(
        "--max-quarantine-rate",
        type=float,
        default=0.01,
        help="Fail if the quarantined proportion exceeds this (default: 1%).",
    )
    parser.add_argument(
        "--allow-empty-source",
        action="store_true",
        help="Permit an empty bronze table instead of failing.",
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
        f"Validated {result['source_rows']:,} rows: "
        f"{result['valid_rows']:,} valid, "
        f"{result['quarantine_rows']:,} quarantined."
    )
    if result["source_rows"] == 0:
        if not args.allow_empty_source:
            logger.error(
                f"{validation.bronze_table} is empty — upstream ingestion may have failed."
            )
            sys.exit(1)
        logger.warning(f"{validation.bronze_table} is empty; skipping quarantine-rate check.")
    else:
        rate = result["quarantine_rows"] / result["source_rows"]
        if rate > args.max_quarantine_rate:
            logger.error(
                f"Quarantine rate {rate:.2%} exceeds threshold {args.max_quarantine_rate:.2%} "
                f"({result['quarantine_rows']:,} of {result['source_rows']:,} rows)."
            )
            sys.exit(1)
        logger.info(f"Quarantine rate {rate:.2%}, within threshold.")
