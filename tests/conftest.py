"""Shared pytest fixtures for the whole test suite."""

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark(tmp_path_factory: pytest.TempPathFactory) -> SparkSession:
    """Session-scoped local Spark session for unit tests.

    Session scope (not function) because creating a SparkSession takes ~5 seconds;
    sharing one across tests cuts the full suite time by an order of magnitude.

    spark.sql.shuffle.partitions=1: defaults to 200, which is wasteful for the
    tiny dataframes used in tests. One partition makes tests finish in milliseconds.
    """
    warehouse = tmp_path_factory.mktemp("warehouse")
    return (
        SparkSession.builder.master("local[*]")
        .appName("rl-tests")
        .config("spark.sql.warehouse.dir", str(warehouse))
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
