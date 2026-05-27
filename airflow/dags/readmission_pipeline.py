"""Readmission lakehouse — end-to-end medallion pipeline.

Turns the hand-run sequence into one orchestrated DAG:

    trigger_bronze >> trigger_silver >> run_dbt_build

  trigger_bronze : Databricks job "[dev ibralhindi] bronze-ingestion"
                   (for_each over 14 FHIR resources -> rl_dev.bronze.*)
  trigger_silver : Databricks job "[dev ibralhindi] silver-validation"
                   (Pydantic validation -> rl_dev.silver.*_valid / *_quarantine)
  run_dbt_build  : dbt build -> silver models + SCD2 snapshots + gold star
                   schema + data tests, in one DAG-ordered run.

Auth:
  - Databricks operators authenticate via the `databricks_default` connection
    (service-principal OAuth M2M).
  - dbt uses its own profiles.yml; we pass it the SAME service principal as env
    vars. client_id is not secret (also in databricks.yml); the secret comes
    from the Airflow Variable `databricks_sp_client_secret`.
"""

from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

# Databricks job ids (dev), from `databricks jobs list`. Stable across
# `bundle deploy` updates; only change if the bundle is destroyed + recreated.
# Using the id (not the "[dev ibralhindi] ..." name) keeps the DAG independent
# of the dev-mode name prefix.
BRONZE_JOB_ID = 73579121572904
SILVER_JOB_ID = 122673186058194

# SP application id — NOT secret (also committed in databricks.yml). The OAuth
# secret is the Airflow Variable databricks_sp_client_secret.
SP_CLIENT_ID = "e305daca-ddaa-4446-a3f4-5c89df23a17c"

default_args = {
    "owner": "ibrahim",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,  # 2 -> 4 -> 8 min between retries
    "max_retry_delay": timedelta(minutes=15),
    "execution_timeout": timedelta(minutes=45),  # per-task ceiling; a hung task is
    # killed -> on_kill cancels the
    # Databricks run -> cluster stops billing
}

with DAG(
    dag_id="readmission_pipeline",
    description="Medallion refresh: bronze -> silver -> dbt (silver + gold).",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 5, 1, tz="UTC"),
    schedule="@daily",  # realistic cadence; DAG stays PAUSED — trigger manually
    catchup=False,  # don't backfill a run for every day since start_date
    tags=["readmission", "databricks", "dbt", "medallion"],
    dagrun_timeout=timedelta(hours=2),  # whole-run backstop (normal run ~42 min)
    max_consecutive_failed_dag_runs=2,
) as dag:
    trigger_bronze = DatabricksRunNowOperator(
        task_id="trigger_bronze",
        databricks_conn_id="databricks_default",
        job_id=BRONZE_JOB_ID,
    )

    trigger_silver = DatabricksRunNowOperator(
        task_id="trigger_silver",
        databricks_conn_id="databricks_default",
        job_id=SILVER_JOB_ID,
    )

    run_dbt_build = BashOperator(
        task_id="run_dbt_build",
        # `dbt deps` installs dbt_utils (gitignored, so absent from the mounted
        # project). The cluster may be terminated — dbt's connection triggers a
        # start and waits (the SP has CAN_RESTART), so this task runs ~4 min
        # longer on a cold cluster.
        bash_command=(
            "cd /opt/airflow/dbt && "
            "dbt deps && "
            "dbt build --profiles-dir /opt/airflow/dbt-profiles --target airflow"
        ),
        env={
            "DATABRICKS_CLIENT_ID": SP_CLIENT_ID,
            "DATABRICKS_CLIENT_SECRET": "{{ var.value.databricks_sp_client_secret }}",
        },
        # append_env=True keeps PATH so the `dbt` binary is found. Without it,
        # `env` REPLACES the whole environment and the shell can't locate dbt.
        append_env=True,
    )

    trigger_bronze >> trigger_silver >> run_dbt_build
