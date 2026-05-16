output "application_id" {
  value       = azuread_application.this.client_id
  description = "Application (client) ID. This is the AZURE_CLIENT_ID secret GitHub Actions needs."
}

output "service_principal_object_id" {
  value       = azuread_service_principal.this.object_id
  description = "Object ID of the service principal. Used as principal_id in role assignments."
}

output "application_object_id" {
  value       = azuread_application.this.object_id
  description = "Object ID of the application (distinct from the SP's object ID). Useful for some advanced operations."
}
