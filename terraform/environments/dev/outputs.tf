# Outputs surface resource attributes for human use (CLI inspection) and for
# downstream consumption (other Terraform configs, CI workflows).

output "resource_group_name" {
  value       = azurerm_resource_group.main.name
  description = "Main resource group name."
}

output "storage_account_name" {
  value       = module.storage.name
  description = "ADLS Gen2 storage account name."
}

output "storage_dfs_endpoint" {
  value       = module.storage.primary_dfs_endpoint
  description = "ADLS Gen2 DFS endpoint URL."
}

output "key_vault_uri" {
  value       = module.keyvault.vault_uri
  description = "Key Vault HTTPS URI."
}

output "databricks_workspace_url" {
  value       = module.databricks.workspace_url
  description = "Databricks workspace UI URL."
}

output "databricks_access_connector_principal_id" {
  value       = module.databricks.access_connector_principal_id
  description = "Object ID of the Databricks access connector's managed identity."
}

output "github_actions_client_id" {
  value       = module.identity.application_id
  description = "AZURE_CLIENT_ID for GitHub Actions OIDC."
}

output "github_actions_tenant_id" {
  value       = var.tenant_id
  description = "AZURE_TENANT_ID for GitHub Actions OIDC."
}

output "github_actions_subscription_id" {
  value       = var.subscription_id
  description = "AZURE_SUBSCRIPTION_ID for GitHub Actions OIDC."
  sensitive   = true # Mark sensitive so it doesn't print in plan output unprompted.
}
