"""Shared pytest fixtures for the whole test suite."""

import pytest
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """Session-scoped local Spark session for unit tests.

    Session scope (not function) because creating a SparkSession takes ~5 seconds;
    sharing one across tests cuts the full suite time by an order of magnitude.

    spark.sql.shuffle.partitions=1: defaults to 200, which is wasteful for the
    tiny dataframes used in tests. One partition makes tests finish in milliseconds.
    """
    return (
        SparkSession.builder.master("local[*]")
        .appName("rl-bronze-tests")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")  # skip the localhost:4040 web UI
        .getOrCreate()
    )


@pytest.fixture(scope="session")
def delta_spark(tmp_path_factory: pytest.TempPathFactory) -> SparkSession:
    """Spark session with Delta Lake, for integration tests that write tables.

    Separate from the `spark` fixture because Delta needs extra JVM packages
    and a warehouse directory. The first run downloads jars, so it's slow once
    and fast afterwards.
    """
    warehouse = tmp_path_factory.mktemp("warehouse")
    builder = (
        SparkSession.builder.master("local[*]")
        .appName("rl-integration-tests")
        .config("spark.sql.warehouse.dir", str(warehouse))
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()
