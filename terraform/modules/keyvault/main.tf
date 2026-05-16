# Azure Key Vault.
#
# Three notable behaviours:
# - Soft delete is ALWAYS on in azurerm 4.x — Azure removed the escape hatch.
# - Purge protection is the data-protection guarantee on top of soft delete.
# - RBAC is the modern authorisation model; access policies are legacy.
resource "azurerm_key_vault" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  tenant_id           = var.tenant_id
  sku_name            = "standard" # "premium" adds HSM-backed keys; not needed here

  rbac_authorization_enabled = true

  soft_delete_retention_days = var.soft_delete_retention_days

  purge_protection_enabled = var.purge_protection_enabled

  # Network access. Same Allow/AzureServices pattern as the storage account —
  # acceptable for dev with synthetic data, tighten for prod.
  public_network_access_enabled = true
  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  tags = var.tags
}
