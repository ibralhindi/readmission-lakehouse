"""CLI entrypoint for bronze ingestion — also the Databricks job entry.

Wired in pyproject.toml as a console script. On Databricks, the bundle's
python_wheel_task invokes this function with `--resource-name <NAME>`.
Locally, you can run it via `uv run rl-bronze-ingest --resource-name Patient`
if you have a Spark session available (we won't — this is a cluster-only path).
"""

from __future__ import annotations

import argparse
import logging
import sys

from pyspark.sql import SparkSession

from readmission_lakehouse.bronze.ingest import ingest_resource
from readmission_lakehouse.bronze.resources import BRONZE_RESOURCES

logger = logging.getLogger(__name__)

# Deployment-specific. Hardcoded for the dev environment. Multi-env teams
# would inject these via job parameters or env vars; we're single-env so
# constants in code are honest about the actual coupling.
RAW_BASE = "abfss://raw@rlst3e33.dfs.core.windows.net/synthea"
BRONZE_CATALOG = "rl_dev"
BRONZE_SCHEMA = "bronze"


def main() -> None:
    """Console-script entry point."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Ingest a FHIR resource into the bronze layer.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--resource-name",
        required=True,
        choices=[resource.name for resource in BRONZE_RESOURCES],
        help="FHIR resource type to ingest.",
    )
    args = parser.parse_args()

    resource = next((r for r in BRONZE_RESOURCES if r.name == args.resource_name), None)
    if resource is None:
        logger.error(f"Invalid resource name: {args.resource_name}")
        sys.exit(1)

    spark = SparkSession.builder.getOrCreate()

    source_path = f"{RAW_BASE}/{resource.source_glob}"
    target_table = f"{BRONZE_CATALOG}.{BRONZE_SCHEMA}.{resource.table_name}"

    logger.info(f"Ingesting {resource.name} from {source_path} to {target_table}")
    result = ingest_resource(spark, source_path, target_table)
    logger.info(f"Ingested {result['row_count']} rows to {result['target_table']}")
    logger.info(f"Ingestion run ID: {result['ingestion_run_id']}")
