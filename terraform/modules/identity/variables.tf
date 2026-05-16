variable "application_display_name" {
  type        = string
  description = "Display name for the Azure AD application registration."
}

# Map-based input lets the env config define each federated credential with both
# a stable resource key (the map key, used in Terraform resource addresses) and
# the actual claim subject. Better than list-based for_each because adding/removing
# entries doesn't cause spurious resource churn when ordering shifts.
variable "federated_credentials" {
  type = map(object({
    subject     = string
    description = string
  }))
  description = "Map of federated identity credentials. Each entry trusts a specific OIDC subject claim."
}

variable "github_token_issuer" {
  type        = string
  description = "OIDC token issuer URL. Defaults to GitHub Actions's well-known issuer."
  default     = "https://token.actions.githubusercontent.com"
}

variable "github_token_audience" {
  type        = string
  description = "Expected audience claim in the OIDC token. 'api://AzureADTokenExchange' is the Microsoft-recommended audience."
  default     = "api://AzureADTokenExchange"
}
