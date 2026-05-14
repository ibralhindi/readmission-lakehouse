#!/usr/bin/env bash
# Install Azure CLI, Terraform, and tflint for Phase 3.
# Idempotent — checks for each tool before installing.

set -euo pipefail  # exit on error, undefined var, or pipe failure

echo "==> Updating apt cache and installing prerequisites..."
sudo apt update -qq
sudo apt install -y -qq curl wget gnupg lsb-release apt-transport-https ca-certificates

# Azure CLI: cloud control plane — login, register providers, bootstrap state.
echo "==> Installing Azure CLI..."
if command -v az >/dev/null 2>&1; then
  echo "    already installed: $(az version --query '\"azure-cli\"' -o tsv)"
else
  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
fi

# Terraform: the IaC tool itself. Installed via HashiCorp's APT repo so apt-get upgrade keeps it current.
echo "==> Installing Terraform..."
if command -v terraform >/dev/null 2>&1; then
  echo "    already installed: $(terraform version | head -1)"
else
  # Adds HashiCorp's signing key, then their repo, then installs from apt.
  wget -qO- https://apt.releases.hashicorp.com/gpg \
    | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/hashicorp.list >/dev/null
  sudo apt update -qq
  sudo apt install -y terraform
fi

# tflint: catches deprecated args, unused vars, provider-specific anti-patterns.
# Lighter and faster than terraform's built-in validate; pairs well with it.
echo "==> Installing tflint..."
if command -v tflint >/dev/null 2>&1; then
  echo "    already installed: $(tflint --version | head -1)"
else
  curl -fsSL https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
fi

echo ""
echo "==> Versions installed:"
echo "Azure CLI:  $(az version --query '"azure-cli"' -o tsv)"
echo "Terraform:  $(terraform version | head -1 | awk '{print $2}')"
echo "tflint:     $(tflint --version | head -1 | awk '{print $3}')"
