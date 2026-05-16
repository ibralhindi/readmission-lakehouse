# --- Azure AD application registration ---
# The "application" is the identity definition in Entra ID — name, owners,
# permissions metadata. The actual identity that holds RBAC assignments and
# is used at runtime is the SERVICE PRINCIPAL, created below from this application.
#
# Distinction worth knowing for interviews:
# - application:        the global definition (one per AAD tenant by app id)
# - service principal:  the local manifestation in this tenant that gets RBAC
#                       (for first-party apps you can have many SPs in different tenants
#                       trusting one application; for our use it's 1:1)
resource "azuread_application" "this" {
  display_name = var.application_display_name
}

# --- Service principal ---
# This is the thing role assignments target. principal_id (object_id) is the value
# that goes in azurerm_role_assignment.principal_id.
resource "azuread_service_principal" "this" {
  client_id = azuread_application.this.client_id
}

# --- Federated identity credentials ---
# Each entry trusts ONE specific OIDC subject claim. The subject claim is what
# GitHub puts in the token to identify "who's running" — combinations of
# repo, branch, pull_request status, environment, etc.
#
# Subject claim formats (you'll see all of these in real CI setups):
#   repo:OWNER/REPO:ref:refs/heads/<branch>     -> a specific branch
#   repo:OWNER/REPO:ref:refs/tags/<tag>         -> a specific tag
#   repo:OWNER/REPO:pull_request                -> ANY pull request from the repo
#   repo:OWNER/REPO:environment:<env-name>      -> a specific GitHub environment
#
# The trust is exact-match on subject — you can't wildcard. Hence one credential
# per subject pattern.
resource "azuread_application_federated_identity_credential" "this" {
  for_each = var.federated_credentials

  application_id = azuread_application.this.id
  subject        = each.value.subject
  display_name   = each.key
  description    = each.value.description
  audiences      = [var.github_token_audience]
  issuer         = var.github_token_issuer
}
