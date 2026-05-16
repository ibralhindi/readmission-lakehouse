# --- Read tfstate backend RG/SA names from the backend config (for RBAC scoping) ---
# We need to grant the GH Actions SP data-plane access to the tfstate SA so CI
# can read/write state. Looking up the SA dynamically rather than hardcoding.
data "azurerm_storage_account" "tfstate" {
  name                = "${var.project_prefix}tfstate${var.project_suffix}"
  resource_group_name = "${var.project_prefix}-rg-tfstate"
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
  scope                = data.azurerm_storage_account.tfstate.id
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
