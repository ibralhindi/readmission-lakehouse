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

output "uc_catalog_name" {
  value       = databricks_catalog.main.name
  description = "Unity Catalog catalog name for the project."
}

output "uc_schemas" {
  value       = [for k, _ in databricks_schema.this : "${databricks_catalog.main.name}.${k}"]
  description = "Fully-qualified UC schema names (catalog.schema)."
}

output "uc_external_locations" {
  value       = { for k, v in databricks_external_location.this : k => v.url }
  description = "Map of container name to external location URL."
}

output "agent_acr_login_server" {
  value       = azurerm_container_registry.agent.login_server
  description = "ACR login server for building/pushing the agent image."
}

output "agent_identity_client_id" {
  value       = azurerm_user_assigned_identity.agent.client_id
  description = "Client ID of the agent's managed identity (set as AZURE_CLIENT_ID on the Container App)."
}

output "agent_container_app_environment_id" {
  value       = azurerm_container_app_environment.agent.id
  description = "Container Apps environment ID (used in 10.5d)."
}

output "agent_url" {
  value       = "https://${azurerm_container_app.agent.latest_revision_fqdn}"
  description = "Public HTTPS URL of the deployed agent."
}
