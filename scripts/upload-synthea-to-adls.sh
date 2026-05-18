#!/usr/bin/env bash
# Uploads the 14 bronzed Synthea NDJSON files to the project ADLS raw container.
# Uses azcopy with AAD auth (azcopy login required first).
# Idempotent — azcopy will skip files that already exist with matching length.

set -euo pipefail

# azcopy's default interactive OAuth flow rejects personal Microsoft accounts.
# Delegate to the az CLI's existing token instead.
export AZCOPY_AUTO_LOGIN_TYPE=AZCLI

# --- Config ---
SOURCE_DIR="${HOME}/projects/readmission-lakehouse/data/synthea/output/fhir"
ACCOUNT_NAME="rlst3e33"
CONTAINER="raw"
DEST_BASE="https://${ACCOUNT_NAME}.dfs.core.windows.net/${CONTAINER}/synthea"

# Bronzed resources (the 14 we agreed in Phase 2's data dictionary). Other
# resources are left local to keep storage spend minimal — we can upload more
# later if needed.
BRONZED_RESOURCES=(
  "Patient.ndjson"
  "Encounter.ndjson"
  "Condition.ndjson"
  "Procedure.ndjson"
  "Observation.ndjson"
  "MedicationRequest.ndjson"
  "Immunization.ndjson"
  "Claim.ndjson"
  "AllergyIntolerance.ndjson"
  "CarePlan.ndjson"
  "CareTeam.ndjson"
  "DocumentReference.ndjson"
)

# These two have the hospital-exporter naming pattern with a timestamp suffix.
# We glob them so it works regardless of the actual timestamp value.
TIMESTAMPED_GLOBS=(
  "Organization.*.ndjson"
  "Practitioner.*.ndjson"
)

# --- Upload non-timestamped files ---
echo "==> Uploading 12 patient-level resources..."
for filename in "${BRONZED_RESOURCES[@]}"; do
  src="${SOURCE_DIR}/${filename}"
  if [[ ! -f "$src" ]]; then
    echo "  SKIP $filename (not found at $src)"
    continue
  fi
  echo "  -> ${filename} ($(du -h "$src" | cut -f1))"
  azcopy copy "$src" "${DEST_BASE}/${filename}" --overwrite=ifSourceNewer --output-level=quiet
done

# --- Upload timestamped files ---
echo "==> Uploading 2 organization-level resources (timestamped pattern)..."
for pattern in "${TIMESTAMPED_GLOBS[@]}"; do
  for src in ${SOURCE_DIR}/${pattern}; do
    if [[ ! -f "$src" ]]; then
      echo "  SKIP pattern $pattern (no matches)"
      continue
    fi
    filename=$(basename "$src")
    echo "  -> ${filename} ($(du -h "$src" | cut -f1))"
    azcopy copy "$src" "${DEST_BASE}/${filename}" --overwrite=ifSourceNewer --output-level=quiet
  done
done

echo ""
echo "==> Upload complete. Verifying with az CLI..."
az storage blob list \
  --account-name "$ACCOUNT_NAME" \
  --container-name "$CONTAINER" \
  --prefix "synthea/" \
  --auth-mode login \
  --query "[].{name:name, size:properties.contentLength}" \
  --output table
