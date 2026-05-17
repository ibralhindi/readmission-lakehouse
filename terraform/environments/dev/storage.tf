# --- Call the storage module ---
module "storage" {
  source              = "../../modules/storage"
  name                = local.storage_account_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  containers          = ["bronze", "silver", "gold", "raw"]
  tags                = local.common_tags
}

# --- Grant the developer data-plane access ---
# Subscription Owner does NOT include
# blob read/write. We need this assignment so we can manually upload Synthea
# NDJSON to `raw` from the CLI and verify Databricks ingestion later.
resource "azurerm_role_assignment" "developer_storage_blob_data_contributor" {
  scope                = module.storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.developer_object_id
}
