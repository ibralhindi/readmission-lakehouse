# --- Databricks workspace ---
# The workspace is the Azure-side representation of the Databricks control plane.
# It's free to exist; compute charges only accrue when clusters run.
#
# managed_resource_group_name: Azure auto-creates this RG to hold Databricks's
# internal infrastructure (VMs, NICs, NSGs, the workspace storage). We name it,
# but cannot modify its contents — Azure denies write perms on it.
resource "azurerm_databricks_workspace" "this" {
  name                        = var.workspace_name
  resource_group_name         = var.resource_group_name
  location                    = var.location
  sku                         = var.sku
  managed_resource_group_name = var.managed_resource_group_name

  tags = var.tags
}

# --- Access Connector ---
# A managed identity attached to Databricks. When notebooks/jobs authenticate
# to external Azure services, they present this identity. We grant the identity
# RBAC on the storage account below — no service principal secrets, no PATs.
#
# 2024+ best practice: access connector + managed identity replaces the legacy
# pattern of service principals with shared secrets in cluster init scripts.
resource "azurerm_databricks_access_connector" "this" {
  name                = var.access_connector_name
  resource_group_name = var.resource_group_name
  location            = var.location

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# --- RBAC: grant the access connector's identity Storage Blob Data Contributor ---
# This is the wire that lets Databricks read/write bronze/silver/gold/raw.
# Without this assignment, every Databricks query against ADLS Gen2 fails with 403.
resource "azurerm_role_assignment" "access_connector_storage" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"

  principal_id = azurerm_databricks_access_connector.this.identity[0].principal_id
}
