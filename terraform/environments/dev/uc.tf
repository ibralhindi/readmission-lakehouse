# Unity Catalog resources for the dev environment.
# Organised top-down: credential → external locations → catalog → schemas.

# --- Storage credential ---
# Wraps the access connector's system-assigned managed identity. Single credential
# reused by all external locations; one credential = one cloud identity to manage.
resource "databricks_storage_credential" "access_connector" {
  name    = "${var.project_prefix}-access-connector-${var.environment}"
  comment = "Wraps rl-ac-3e33 managed identity for UC external location access."

  azure_managed_identity {
    access_connector_id = module.databricks.access_connector_id
  }
}

# --- External locations ---
# Pairs (cloud path, credential). UC enforces "data at this path is accessed via
# this credential". Even though the access connector already has Storage Blob Data
# Blob data access on the storage account is granted to the access connector in
# the Databricks module; UC requires THIS additional layer of binding before
# tables/queries can read from these paths.
locals {
  uc_containers = ["bronze", "silver", "gold", "raw"]
}

resource "databricks_external_location" "this" {
  for_each = toset(local.uc_containers)

  name            = "${var.project_prefix}-${each.key}-${var.environment}"
  credential_name = databricks_storage_credential.access_connector.name
  comment         = "External location for the ${each.key} container."
  url             = "abfss://${each.key}@${module.storage.name}.dfs.core.windows.net/"
}

# --- Catalog ---
# Our project-owned catalog. Distinct from the auto-created rl_dbx_3e33 which
# uses Databricks-managed storage; ours uses our own ADLS via external locations.
resource "databricks_catalog" "main" {
  name           = "${var.project_prefix}_${var.environment}"
  comment        = "Main catalog for the readmission lakehouse project."
  isolation_mode = "ISOLATED" # Binds the catalog to this workspace only.

  # Catalog default managed storage. In practice this stays nearly empty because
  # every schema (bronze/silver/gold) overrides with its own storage_root.
  # Lives under raw/ with an underscore prefix to signal "infra, not source data".
  storage_root = "${databricks_external_location.this["raw"].url}_catalog_default"

  depends_on = [databricks_external_location.this]
}

# --- Schemas (with per-schema managed storage) ---
# Each schema's storage_root points to a sub-path of its layer's external location.
# Why "/managed" suffix instead of using the container root: keeps managed-table
# physical storage separate from any other writes we might do directly to the
# container (e.g. checkpoints, _delta_log archives). Convention, not required.
locals {
  uc_schemas = {
    bronze = "Bronze layer: raw ingested data with ingestion metadata only."
    silver = "Silver layer: cleansed, deduplicated, Pydantic-validated."
    gold   = "Gold layer: Kimball star schema for analytics."
  }
}

resource "databricks_schema" "this" {
  for_each = local.uc_schemas

  catalog_name = databricks_catalog.main.name
  name         = each.key
  comment      = each.value

  # Path where managed tables for this schema physically live.
  # Sub-path of the external location at the container root. UC permits
  # schema storage_root to be a sub-path of a registered external location.
  # Referencing the external location URL (not a hand-built string) gives
  # Terraform an implicit dependency: depends_on cannot use each.key.
  storage_root = "${databricks_external_location.this[each.key].url}managed"
}
