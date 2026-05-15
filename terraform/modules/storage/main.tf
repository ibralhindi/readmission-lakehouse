# ADLS Gen2 storage account.
#
# Two critical-and-immutable flags decided at creation:
#   - is_hns_enabled = true  → makes this ADLS Gen2 (filesystem semantics).
#   - account_kind   = "StorageV2"  → required for HNS and all modern features.
#
# Changing either of these post-creation requires destroy + recreate.
resource "azurerm_storage_account" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location

  # --- Tier and replication ---
  # Standard_LRS: cheapest tier, single-region 3-replica.
  # For prod multi-region you'd use GRS or RA-GRS; for dev portfolio LRS is correct.
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  # --- ADLS Gen2 (HNS) ---
  is_hns_enabled = true

  # --- Security defaults ---
  # min_tls_version: legacy TLS 1.0/1.1 are deprecated and have known vulns.
  # allow_nested_items_to_be_public: blob-level public access. Forcing false at the
  #   account level prevents accidental container-level public exposure.
  # shared_access_key_enabled: true allows fall-back key auth. We'll need this until
  #   Databricks is fully wired via managed identity; tighten after.
  # public_network_access_enabled: true for dev to keep network simple. Prod would
  #   set this false and use private endpoints from a VNet.
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = true
  public_network_access_enabled   = true

  # --- Network rules ---
  # Default action "Allow" = open to public internet (filtered only by firewall on
  # client side, e.g. corporate proxies). Acceptable for a dev portfolio with
  # synthetic data. For prod: switch to "Deny" with ip_rules for known CIs and
  # virtual_network_subnet_ids for the Databricks data plane.
  network_rules {
    default_action = "Allow"
    bypass         = ["AzureServices"] # Azure-internal services bypass the rule
  }

  # --- Blob lifecycle / recovery ---
  # We DO NOT enable blob versioning because the bronze/silver/gold layers use
  # Delta Lake, which has its own versioning (time travel). Blob versioning on
  # top would be wasteful — Delta would create new files anyway, and versioning
  # would keep old versions of overwritten Parquet files (which we can ignore
  # because Delta only references current ones).
  #
  # 7-day soft delete is cheap insurance against `terraform destroy` mistakes.
  blob_properties {
    delete_retention_policy {
      days = 7
    }
    container_delete_retention_policy {
      days = 7
    }
  }

  tags = var.tags
}

# Containers (logical folders within the storage account).
# for_each over the input list. Each container is private (no anonymous access).
resource "azurerm_storage_container" "this" {
  for_each              = toset(var.containers)
  name                  = each.key
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}
