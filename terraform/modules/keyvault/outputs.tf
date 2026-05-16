output "id" {
  value       = azurerm_key_vault.this.id
  description = "Full Azure resource ID of the Key Vault."
}

output "name" {
  value       = azurerm_key_vault.this.name
  description = "Name of the Key Vault."
}

# vault_uri is the HTTPS endpoint apps use to read/write secrets,
# e.g. https://rl-kv-3e33.vault.azure.net/
output "vault_uri" {
  value       = azurerm_key_vault.this.vault_uri
  description = "HTTPS URI of the Key Vault for SDK/CLI access."
}
