output "workspace_id" {
  value       = azurerm_databricks_workspace.this.id
  description = "Full Azure resource ID of the Databricks workspace."
}

output "workspace_url" {
  value       = "https://${azurerm_databricks_workspace.this.workspace_url}"
  description = "HTTPS URL to access the Databricks workspace UI."
}

output "workspace_resource_id" {
  value       = azurerm_databricks_workspace.this.workspace_id
  description = "The numeric Databricks workspace ID (NOT the Azure resource ID — used by the Databricks provider)."
}

output "access_connector_id" {
  value       = azurerm_databricks_access_connector.this.id
  description = "Full Azure resource ID of the access connector. Referenced when configuring external locations."
}

output "access_connector_principal_id" {
  value       = azurerm_databricks_access_connector.this.identity[0].principal_id
  description = "Object ID of the access connector's managed identity. Useful for additional RBAC assignments."
}
