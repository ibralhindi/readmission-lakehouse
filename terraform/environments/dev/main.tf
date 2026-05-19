# Terraform configuration and backend.
#
# required_version sets the minimum CLI version this code is known to work with.
# required_providers pins providers to a compatible major version (semver-style ~>).
# The backend block declares "store state remotely in Azure Storage"; the actual
# storage account/container/key come from the partial-config file at init time
# (terraform init -backend-config=backend.conf).
terraform {
  required_version = ">= 1.10"

  required_providers {
    # Manages Azure resources (RG, storage, key vault, databricks, etc.).
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    # Manages Azure Entra ID (formerly Azure AD) objects: app registrations,
    # service principals, group memberships, federated credentials for OIDC.
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
    # Generates random suffixes for any resource names we don't pre-seed.
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
  }

  # Partial backend config: real values come from backend.conf via
  # `terraform init -backend-config=backend.conf`. Keeps subscription-identifying
  # storage account names out of git.
  backend "azurerm" {}
}

# azurerm provider. The empty `features {}` block is REQUIRED by the provider
# even when you have no feature flags to set — it's how azurerm declares
# "yes, I've seen the features block exists." Removing it is a syntax error.
provider "azurerm" {
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id

  features {
    # Future: set per-resource-type behaviour here (e.g. key_vault delete recovery,
    # virtual_machine OS disk handling). Empty for now; the block must still exist.
  }
}

# azuread provider: only needs tenant_id; auth is inherited from az login.
provider "azuread" {
  tenant_id = var.tenant_id
}

# Databricks provider for workspace-level Unity Catalog resources (storage credential,
# external locations, catalogs, schemas). Authenticates via the Azure CLI session
# locally; in CI, picks up ARM_CLIENT_ID/TENANT/SUBSCRIPTION from OIDC env vars.
#
# Distinction worth knowing: there are two Databricks API layers — account-level
# (for metastores, users, accounts admin) and workspace-level (everything else).
# This provider config targets workspace-level only, which is all we need.
provider "databricks" {
  host                        = module.databricks.workspace_url
  azure_workspace_resource_id = module.databricks.workspace_id
}
