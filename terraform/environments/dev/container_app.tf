# --- Container registry (holds the agent image) ---
# Basic SKU is plenty for one image. admin_enabled = false: no static admin
# user/password — pulls are authorised via the agent's managed identity
# (AcrPull), the same no-secrets discipline as everywhere else.
resource "azurerm_container_registry" "agent" {
  name                = "${var.project_prefix}acr${var.project_suffix}" # alphanumeric only, globally unique
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = local.common_tags
}

# --- User-assigned managed identity for the agent ---
# This is the identity DefaultAzureCredential resolves to in the cloud. It reads
# Key Vault and pulls from ACR — no stored secret anywhere.
resource "azurerm_user_assigned_identity" "agent" {
  name                = "${var.project_prefix}-agent-mi-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.common_tags
}

# --- Log Analytics workspace (Container Apps logs land here) ---
# Lets us read container stdout/stderr to debug the boot + MI auth chain.
resource "azurerm_log_analytics_workspace" "agent" {
  name                = "${var.project_prefix}-agent-logs-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}

# --- Container Apps environment (the hosting environment) ---
resource "azurerm_container_app_environment" "agent" {
  name                       = "${var.project_prefix}-agent-env-${var.environment}"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.agent.id
  tags                       = local.common_tags
}

# --- Role grants for the agent identity ---
# (a) Pull the image from our registry.
resource "azurerm_role_assignment" "agent_acr_pull" {
  scope                            = azurerm_container_registry.agent.id
  role_definition_name             = "AcrPull"
  principal_id                     = azurerm_user_assigned_identity.agent.principal_id
  skip_service_principal_aad_check = true # avoids AAD replication-lag failures on a fresh MI
}

# (b) Read secrets from Key Vault. rl-kv-3e33 is RBAC-mode, so this is a role
#     assignment, not an access policy. "Key Vault Secrets User" = get/list
#     secrets only — least privilege (not Officer/Administrator).
resource "azurerm_role_assignment" "agent_kv_secrets" {
  scope                            = module.keyvault.id
  role_definition_name             = "Key Vault Secrets User"
  principal_id                     = azurerm_user_assigned_identity.agent.principal_id
  skip_service_principal_aad_check = true
}

# --- The agent Container App (the no-secrets payoff) ---
resource "azurerm_container_app" "agent" {
  name                         = "${var.project_prefix}-agent-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.agent.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.common_tags

  # One identity, two uses: pulls the image from ACR, and (via
  # DefaultAzureCredential inside the app) reads secrets from Key Vault.
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.agent.id]
  }

  # Pull via the MI (AcrPull from 10.5b) — no registry username/password.
  registry {
    server   = azurerm_container_registry.agent.login_server
    identity = azurerm_user_assigned_identity.agent.id
  }

  ingress {
    external_enabled = true
    target_port      = 8501
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0 # scale to zero when idle — no compute cost between demos
    max_replicas = 1

    container {
      name   = "agent"
      image  = "${azurerm_container_registry.agent.login_server}/rl-agent:v1"
      cpu    = 1.0
      memory = "2Gi"

      # Override the start command to add proxy-friendly Streamlit flags — its
      # XSRF/CORS checks otherwise block the websocket behind the Container Apps
      # ingress. Set here (not the Dockerfile) so we can tweak without rebuilding.
      command = ["streamlit", "run", "src/readmission_lakehouse/agent/app.py"]
      args = [
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
      ]

      # AZURE_CLIENT_ID tells DefaultAzureCredential which user-assigned identity
      # to use. The rest are NON-secret identifiers (same as the old .env). The
      # real secrets are fetched from Key Vault at runtime via the MI.
      env {
        name  = "AZURE_CLIENT_ID"
        value = azurerm_user_assigned_identity.agent.client_id
      }
      env {
        name  = "DATABRICKS_SERVER_HOSTNAME"
        value = "adb-7405614307158980.0.azuredatabricks.net"
      }
      env {
        name  = "DATABRICKS_HTTP_PATH"
        value = "/sql/1.0/warehouses/4cefe31ffc4390a9"
      }
      env {
        name  = "DATABRICKS_CLIENT_ID"
        value = "e305daca-ddaa-4446-a3f4-5c89df23a17c"
      }
    }
  }

  # Don't create the app until the MI can actually pull + read KV, or the first
  # revision fails to start.
  depends_on = [
    azurerm_role_assignment.agent_acr_pull,
    azurerm_role_assignment.agent_kv_secrets,
  ]
}
