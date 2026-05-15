# The project's main resource group. Lifecycle-distinct from the tfstate RG
# (which lives outside Terraform's scope) so `terraform destroy` safely removes
# everything in this RG without touching the state backend.
resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}
