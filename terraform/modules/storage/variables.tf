# Inputs to the storage module.
# This module creates one ADLS Gen2 storage account and N containers within it.

variable "name" {
  type        = string
  description = "Storage account name. Must be 3-24 lowercase alphanumeric chars, globally unique across Azure."

  validation {
    # Azure's hard rule for storage account names. Hyphens are forbidden,
    # uppercase is forbidden, length is strict.
    condition     = can(regex("^[a-z0-9]{3,24}$", var.name))
    error_message = "Storage account name must be 3-24 lowercase alphanumeric chars (no hyphens)."
  }
}

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group to create the storage account in."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "containers" {
  type        = list(string)
  description = "Container names to create within the storage account."
  default     = ["bronze", "silver", "gold", "raw"]
  validation {
    condition     = alltrue([for c in var.containers : can(regex("^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$", c))])
    error_message = "Every container name must be 3-63 lowercase alphanumeric or hyphens, start and end with alphanumeric."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the storage account."
  default     = {}
}
