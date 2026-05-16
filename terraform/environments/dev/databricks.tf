# Databricks workspace + access connector.
# The managed RG name composed from the main RG name; this is convention but
# any unique name works.
module "databricks" {
  source                      = "../../modules/databricks"
  workspace_name              = local.databricks_workspace_name
  access_connector_name       = local.access_connector_name
  resource_group_name         = azurerm_resource_group.main.name
  managed_resource_group_name = "${local.resource_group_name}-dbx-managed"
  location                    = azurerm_resource_group.main.location
  sku                         = "premium"
  storage_account_id          = module.storage.id
  tags                        = local.common_tags
}
