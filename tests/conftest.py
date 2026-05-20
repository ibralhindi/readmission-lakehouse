"""Shared pytest fixtures for the whole test suite."""

import pytest
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
