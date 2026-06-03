#!/usr/bin/env bash
# Uploads the 14 bronzed Synthea NDJSON files to the project ADLS raw container.
# Uses azcopy with AAD auth (azcopy login required first).
# Idempotent — azcopy will skip files that already exist with matching length.

set -euo pipefail

# azcopy's default interactive OAuth flow rejects personal Microsoft accounts.
# Delegate to the az CLI's existing token instead.
export AZCOPY_AUTO_LOGIN_TYPE=AZCLI
# Default concurrency (256 on 16 cores) overwhelms slow uplinks; 4 is safer.
export AZCOPY_CONCURRENCY_VALUE="${AZCOPY_CONCURRENCY_VALUE:-4}"

# --- Config ---
SOURCE_DIR="${HOME}/projects/readmission-lakehouse/data/synthea/output/fhir"
ACCOUNT_NAME="rlst3e33"
CONTAINER="raw"
# Blob endpoint uses block-blob Put Block uploads; the dfs endpoint uses append
# PATCH and times out on slow home uplinks even for small .gz files.
DEST_BASE="https://${ACCOUNT_NAME}.blob.core.windows.net/${CONTAINER}/synthea"

# Bronzed resources (the 14 FHIR resources selected for the bronze layer). Other
# resources are left local to keep storage spend minimal — we can upload more
# later if needed.
BRONZED_RESOURCES=(
  "Patient.ndjson.gz"
  "Encounter.ndjson.gz"
  "Condition.ndjson.gz"
  "Procedure.ndjson.gz"
  "Observation.ndjson.gz"
  "MedicationRequest.ndjson.gz"
  "Immunization.ndjson.gz"
  "Claim.ndjson.gz"
  "AllergyIntolerance.ndjson.gz"
  "CarePlan.ndjson.gz"
  "CareTeam.ndjson.gz"
  "DocumentReference.ndjson.gz"
)

# These two have the hospital-exporter naming pattern with a timestamp suffix.
# We glob them so it works regardless of the actual timestamp value.
TIMESTAMPED_GLOBS=(
  "Organization.*.ndjson.gz"
  "Practitioner.*.ndjson.gz"
)

# Failed uploads can leave 0-byte ADLS stubs; azcopy --overwrite=ifSourceNewer
# treats those as present and skips, so remove stubs before each transfer.
remove_empty_blob_stub() {
  local blob_name="$1"
  local blob_path="synthea/${blob_name}"
  local size

  size=$(az storage blob show \
    --account-name "$ACCOUNT_NAME" \
    --container-name "$CONTAINER" \
    --name "$blob_path" \
    --auth-mode login \
    --query "properties.contentLength" \
    -o tsv 2>/dev/null) || return 0

  if [[ -z "$size" || "$size" == "0" ]]; then
    echo "  removing empty stub: ${blob_path}"
    az storage blob delete \
      --account-name "$ACCOUNT_NAME" \
      --container-name "$CONTAINER" \
      --name "$blob_path" \
      --auth-mode login \
      --output none
  fi
}

# --- Upload non-timestamped files ---
echo "==> Uploading 12 patient-level resources..."
for filename in "${BRONZED_RESOURCES[@]}"; do
  src="${SOURCE_DIR}/${filename}"
  if [[ ! -f "$src" ]]; then
    echo "  SKIP $filename (not found at $src)"
    continue
  fi
  echo "  -> ${filename} ($(du -h "$src" | cut -f1))"
  remove_empty_blob_stub "$filename"
  azcopy copy "$src" "${DEST_BASE}/${filename}" --overwrite=ifSourceNewer
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
    remove_empty_blob_stub "$filename"
    azcopy copy "$src" "${DEST_BASE}/${filename}" --overwrite=ifSourceNewer
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
