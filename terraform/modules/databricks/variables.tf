variable "workspace_name" {
  type        = string
  description = "Databricks workspace name."

  validation {
    # 3-64 chars, alphanumeric and hyphens
    condition     = can(regex("^[a-zA-Z0-9-]{3,64}$", var.workspace_name))
    error_message = "Workspace name must be 3-64 chars: alphanumeric and hyphens only."
  }
}

variable "access_connector_name" {
  type        = string
  description = "Access connector name (a managed identity Databricks uses for storage access)."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group to create the workspace and access connector in."
}

variable "managed_resource_group_name" {
  type        = string
  description = "Name of the Databricks-managed resource group. Created by Azure on workspace provisioning; we cannot touch its contents."
}

variable "location" {
  type        = string
  description = "Azure region."
}

variable "sku" {
  type        = string
  description = "Databricks workspace SKU: standard, premium, or trial."
  default     = "premium"

  validation {
    condition     = contains(["standard", "premium", "trial"], var.sku)
    error_message = "sku must be one of: standard, premium, trial."
  }
}

variable "storage_account_id" {
  type        = string
  description = "Resource ID of the ADLS Gen2 storage account the access connector needs RBAC on."
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to all resources."
  default     = {}
}
