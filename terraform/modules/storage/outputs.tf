# Outputs exposed by the storage module.
# Consuming environments reference these via module.storage.<output_name>.

output "id" {
  value       = azurerm_storage_account.this.id
  description = "Full Azure resource ID of the storage account."
}

output "name" {
  value       = azurerm_storage_account.this.name
  description = "Name of the storage account."
}

# The DFS (Data Lake Storage) endpoint is the one Spark/Databricks uses to
# access the account in HNS mode. Different from the .blob. endpoint
# (which works but loses HNS semantics).
output "primary_dfs_endpoint" {
  value       = azurerm_storage_account.this.primary_dfs_endpoint
  description = "ADLS Gen2 endpoint URL (https://<name>.dfs.core.windows.net/)."
}

# Map of container name -> resource ID. Useful for downstream RBAC assignments
# that need to scope to a specific container.
output "container_ids" {
  value       = { for k, v in azurerm_storage_container.this : k => v.id }
  description = "Map of container name to container resource ID."
}
