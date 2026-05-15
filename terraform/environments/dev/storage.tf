# --- Call the storage module ---
module "storage" {
  source              = "../../modules/storage"
  name                = local.storage_account_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  containers          = ["bronze", "silver", "gold", "raw"]
  tags                = local.common_tags
}

# --- Grant the running user data-plane access ---
# Subscription Owner does NOT include
# blob read/write. We need this assignment so we can manually upload Synthea
# NDJSON to `raw` from the CLI and verify Databricks ingestion later.
#
# data.azurerm_client_config.current returns info about whoever Terraform is
# authenticating as right now — the user during local dev, the GitHub Actions
# service principal during CI. Granting "the running identity" Contributor
# means both contexts work without special-casing.
data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "current_identity_storage_blob_data_contributor" {
  scope                = module.storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}
