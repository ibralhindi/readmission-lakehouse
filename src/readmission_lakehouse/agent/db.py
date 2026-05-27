"""Databricks SQL warehouse access via service-principal OAuth M2M.

Reuses the Airflow pipeline's service principal (read-only on bronze, read on
gold). Credentials come from the gitignored .env.
"""

from __future__ import annotations

import os
from typing import cast

from databricks.sdk.core import Config, CredentialsProvider, oauth_service_principal
from databricks.sql import connect

from readmission_lakehouse.agent import config  # noqa: F401  # imports => load_dotenv()


def _credential_provider() -> CredentialsProvider:
    # M2M client-credentials flow: exchanges the SP id/secret for a short-lived
    # OAuth bearer token. NOT a static PAT.
    cfg = Config(
        host=f"https://{os.environ['DATABRICKS_SERVER_HOSTNAME']}",
        client_id=os.environ["DATABRICKS_CLIENT_ID"],
        client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
    )
    return cast(CredentialsProvider, oauth_service_principal(cfg))


def query(sql_text: str) -> list[dict]:
    """Run a query against the SQL warehouse; return rows as dicts."""
    with (
        connect(
            server_hostname=os.environ["DATABRICKS_SERVER_HOSTNAME"],
            http_path=os.environ["DATABRICKS_HTTP_PATH"],
            credentials_provider=_credential_provider,
        ) as conn,
        conn.cursor() as cur,
    ):
        cur.execute(sql_text)
        cols = [c[0] for c in cur.description or []]
        return [dict(zip(cols, row)) for row in cur.fetchall()]  # noqa: B905
