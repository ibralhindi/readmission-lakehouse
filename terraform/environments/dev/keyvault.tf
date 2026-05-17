# Call the keyvault module.
module "keyvault" {
  source              = "../../modules/keyvault"
  name                = local.key_vault_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tenant_id           = var.tenant_id
  # purge_protection_enabled defaults to false in the module — correct for dev.
  tags = local.common_tags
}

# Grant the developer full management rights over the KV.
# "Key Vault Administrator" is the broadest role — it can create/read/update/delete
# secrets, keys, AND change RBAC on the vault itself. Reasonable for an admin user;
# we'd give app code only "Key Vault Secrets User" (read-only on secrets).
resource "azurerm_role_assignment" "developer_kv_admin" {
  scope                = module.keyvault.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = var.developer_object_id
}
