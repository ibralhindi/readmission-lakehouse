# Inputs to the keyvault module.

variable "name" {
  type        = string
  description = "Key Vault name. 3-24 chars, must start with a letter, end with alphanumeric, only letters/digits/hyphens."

  validation {
    # Azure's hard rule for Key Vault names. Globally unique across Azure.
    condition     = can(regex("^[a-z][a-z0-9-]{1,22}[a-z0-9]$", var.name))
    error_message = "Key Vault name must be 3-24 chars, start with a letter, end with alphanumeric."
  }
}

variable "resource_group_name" {
  type        = string
  description = "Resource group to create the Key Vault in."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "tenant_id" {
  type        = string
  description = "Azure Entra ID tenant ID for the KV (defines which directory's identities can access)."
}

variable "soft_delete_retention_days" {
  type        = number
  description = "Days a deleted vault/secret is recoverable. Min 7, max 90. Cannot be disabled."
  default     = 7

  validation {
    condition     = var.soft_delete_retention_days >= 7 && var.soft_delete_retention_days <= 90
    error_message = "soft_delete_retention_days must be between 7 and 90."
  }
}

variable "purge_protection_enabled" {
  type        = bool
  description = "If true, soft-deleted vaults cannot be permanently removed before retention expires. Set true for prod, false for dev."
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the Key Vault."
  default     = {}
}
