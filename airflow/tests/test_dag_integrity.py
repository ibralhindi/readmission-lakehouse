"""Integrity checks for the portfolio Airflow DAG."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from airflow.models.dagbag import DagBag

EXPECTED_RETRIES = 2


def test_readmission_pipeline_dag_imports_and_structure() -> None:
    """Verify the DAG imports cleanly and preserves its expected orchestration contract."""
    dag_folder = Path(__file__).resolve().parents[1] / "dags"

    dag_bag = DagBag(dag_folder=str(dag_folder), include_examples=False)

    assert dag_bag.import_errors == {}

    dag = dag_bag.get_dag("readmission_pipeline")
    assert dag is not None
    assert dag.task_ids == ["trigger_bronze", "trigger_silver", "run_dbt_build"]
    assert dag.schedule is None
    assert dag.catchup is False

    trigger_bronze = dag.get_task("trigger_bronze")
    trigger_silver = dag.get_task("trigger_silver")
    run_dbt_build = dag.get_task("run_dbt_build")

    assert trigger_bronze.downstream_task_ids == {"trigger_silver"}
    assert trigger_silver.upstream_task_ids == {"trigger_bronze"}
    assert trigger_silver.downstream_task_ids == {"run_dbt_build"}
    assert run_dbt_build.upstream_task_ids == {"trigger_silver"}

    for task in [trigger_bronze, trigger_silver, run_dbt_build]:
        assert task.retries == EXPECTED_RETRIES
        assert task.retry_delay == timedelta(minutes=2)
