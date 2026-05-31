"""Databricks SQL warehouse access via service-principal OAuth M2M.

Reuses the Airflow pipeline's service principal. Non-secret connection details
(host, http_path, client_id) come from .env; the SP OAuth secret is resolved
from Azure Key Vault via config.get_secret.
"""

from __future__ import annotations

import os

from databricks import sql  # type: ignore[attr-defined, unused-ignore]
from databricks.sdk.core import Config, oauth_service_principal

from readmission_lakehouse.agent.config import get_secret  # also triggers load_dotenv()


def _credential_provider():  # type: ignore[no-untyped-def]
    # M2M client-credentials flow: exchanges the SP id/secret for a short-lived
    # OAuth bearer token. NOT a static PAT. The secret now comes from Key Vault.
    cfg = Config(
        host=f"https://{os.environ['DATABRICKS_SERVER_HOSTNAME']}",
        client_id=os.environ["DATABRICKS_CLIENT_ID"],
        client_secret=get_secret("DATABRICKS_CLIENT_SECRET", "databricks-client-secret"),
    )
    return oauth_service_principal(cfg)


def query(sql_text: str) -> list[dict]:
    """Run a query against the SQL warehouse; return rows as dicts."""
    with (
        sql.connect(
            server_hostname=os.environ["DATABRICKS_SERVER_HOSTNAME"],
            http_path=os.environ["DATABRICKS_HTTP_PATH"],
            credentials_provider=_credential_provider,
        ) as conn,
        conn.cursor() as cur,
    ):
        cur.execute(sql_text)
        cols = [c[0] for c in cur.description or []]
        return [dict(zip(cols, row)) for row in cur.fetchall()]  # noqa: B905
