# Construct the tfstate storage account resource ID from variables we already have.
# This avoids a `data "azurerm_storage_account"` lookup that would require granting
# the CI SP management-plane Reader on the tfstate SA — we'd be reading data we
# can deterministically compute, just to write it back into an attribute. The
# constructed string is identical to what the data source would return.
locals {
  tfstate_storage_account_id = format(
    "/subscriptions/%s/resourceGroups/%s-rg-tfstate/providers/Microsoft.Storage/storageAccounts/%stfstate%s",
    var.subscription_id, var.project_prefix, var.project_prefix, var.project_suffix
  )
}

# --- Identity module: AAD app + SP + 2 federated credentials ---
module "identity" {
  source                   = "../../modules/identity"
  application_display_name = "${var.project_prefix}-gh-actions-${var.environment}"

  federated_credentials = {
    "github-main" = {
      subject     = "repo:ibralhindi/readmission-lakehouse:ref:refs/heads/main"
      description = "Allows apply on main branch."
    }
    "github-pull-request" = {
      subject     = "repo:ibralhindi/readmission-lakehouse:pull_request"
      description = "Allows plan on pull requests (read-only operations only — see role assignments)."
    }
  }
}

# --- Role assignment 1: Contributor on the project RG (management plane) ---
# Lets the SP create / update / destroy resources in rl-rg-dev. This is the
# broadest role most CI SPs need; you could scope it tighter (e.g. specific
# RBAC roles per resource type) but the maintenance burden rarely pays off
# in a single-team project.
resource "azurerm_role_assignment" "ci_contributor_on_rg" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Contributor"
  principal_id         = module.identity.service_principal_object_id
}

# --- Role assignment 2: Storage Blob Data Contributor on tfstate SA
# - Why needed: state blob read/write is a data-plane operation. Subscription
#   Contributor (which the SP doesn't even have) wouldn't include this
resource "azurerm_role_assignment" "ci_storage_blob_contributor_on_tfstate" {
  scope                = local.tfstate_storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = module.identity.service_principal_object_id
}

# --- Role assignment 3: Storage Blob Data Contributor on project SA
# Terraform creates and manages containers; in azurerm 4.x that's a data-plane
# operation. Without this, the next `terraform plan` from CI that touches a container fails 403.
resource "azurerm_role_assignment" "ci_storage_blob_contributor_on_project" {
  scope                = module.storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = module.identity.service_principal_object_id
}

# CI needs management-plane read on the tfstate SA so Terraform can refresh
# state for the `ci_storage_blob_contributor_on_tfstate` role assignment above.
# Storage Blob Data Contributor is data-plane only; reading a role assignment
# is Microsoft.Authorization/roleAssignments/read, which lives in the management
# plane. Reader provides */read at the scope — the narrowest builtin role that
# satisfies this, far better than re-using Contributor.
resource "azurerm_role_assignment" "ci_reader_on_tfstate" {
  scope                = local.tfstate_storage_account_id
  role_definition_name = "Reader"
  principal_id         = module.identity.service_principal_object_id
}
