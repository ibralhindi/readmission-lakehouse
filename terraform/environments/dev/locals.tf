# Locals: computed values derived from variables. Centralised here so resource
# names are constructed in one place and referenced consistently across modules.
#
# Why a separate file: locals.tf is the source of truth for "what each resource
# is called". When you eventually rename or restructure, this is the only file
# that changes.

locals {
  # Resource group name. Composed from prefix + literal + environment.
  # Pattern: <prefix>-rg-<env>  -> e.g. "rl-rg-dev"
  resource_group_name = "${var.project_prefix}-rg-${var.environment}"

  # storage_account_name
  # - Pattern: <prefix>st<suffix>  -> e.g. "rlst3e33"
  # - NO hyphens allowed in storage account names; this is why we don't use the
  #   "<prefix>-st-<suffix>" form.
  storage_account_name = "${var.project_prefix}st${var.project_suffix}"

  # key_vault_name
  # - Pattern: <prefix>-kv-<suffix>  -> e.g. "rl-kv-3e33"
  key_vault_name = "${var.project_prefix}-kv-${var.project_suffix}"

  # databricks_workspace_name
  # - Pattern: <prefix>-dbx-<suffix>  -> e.g. "rl-dbx-3e33"
  databricks_workspace_name = "${var.project_prefix}-dbx-${var.project_suffix}"

  # access_connector_name
  # - Pattern: <prefix>-ac-<suffix>  -> e.g. "rl-ac-3e33"
  access_connector_name = "${var.project_prefix}-ac-${var.project_suffix}"

  # common_tags
  # - A map applied to every taggable resource.
  common_tags = {
    project     = var.project_prefix
    environment = var.environment
    managed-by  = "terraform"
  }
}
