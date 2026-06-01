"""Sample local Synthea FHIR NDJSON exports down to a patient subset.

This CLI makes it cheap to create a small, relationally consistent FHIR sample
for local development and tests. It keeps the logic deliberately simple and
deterministic so downstream pipeline behavior is easier to reproduce.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, cast

import click
import structlog
from pydantic import BaseModel, ConfigDict

# ``structlog`` keeps CLI logs structured so the same events read well locally and in automated
# runs without changing the calling code.
LOGGER = structlog.get_logger(__name__)
# These summary rows are report-like outputs, so freezing them helps tests treat them as immutable
# facts rather than mutable working state.
SAMPLER_MODEL_CONFIG = ConfigDict(frozen=True)

JsonObject = dict[str, Any]


class SamplingSummaryRow(BaseModel):
    """One summary row for the sampler CLI output."""

    model_config = SAMPLER_MODEL_CONFIG

    filename: str
    records_in: int
    records_kept: int
    pct_kept: float


# Click wires this function into a CLI while leaving the pure helper functions easy to unit test.
@click.command()
@click.option(
    "--fhir-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=str),
    required=True,
    help="Directory containing Synthea FHIR NDJSON files.",
)
@click.option(
    "--out-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=str),
    required=True,
    help="Directory to write sampled NDJSON subsets into.",
)
@click.option(
    "--n-patients",
    type=int,
    default=50,
    show_default=True,
    help="Number of patients to keep.",
)
@click.option(
    "--seed",
    type=int,
    default=42,
    show_default=True,
    help="Random seed used to select patients.",
)
def cli(fhir_dir: str, out_dir: str, n_patients: int, seed: int) -> None:
    """Write a patient-filtered subset of local Synthea NDJSON files."""

    # --- Section: Normalize CLI paths ---
    fhir_dir_path = Path(fhir_dir)
    out_dir_path = Path(out_dir)

    # --- Section: Validate required inputs ---
    LOGGER.info(
        "sampling_synthea_fhir",
        fhir_dir=str(fhir_dir_path),
        out_dir=str(out_dir_path),
        n_patients=n_patients,
        seed=seed,
    )
    patient_file = fhir_dir_path / "Patient.ndjson"
    if not patient_file.exists():
        msg = f"Missing required patient file: {patient_file}"
        raise click.ClickException(msg)

    # --- Section: Build the selected patient subset ---
    out_dir_path.mkdir(parents=True, exist_ok=True)
    selected_patient_ids = load_selected_patient_ids(
        patient_file=patient_file,
        n_patients=n_patients,
        seed=seed,
    )
    patient_reference_tokens = build_patient_reference_tokens(selected_patient_ids)

    # --- Section: Sample each resource file and print a summary ---
    summaries: list[SamplingSummaryRow] = []
    for input_path in iter_ndjson_files(fhir_dir_path):
        resource_type = derive_resource_type(input_path)
        output_path = out_dir_path / input_path.name
        summaries.append(
            sample_one_file(
                input_path=input_path,
                output_path=output_path,
                resource_type=resource_type,
                selected_patient_ids=selected_patient_ids,
                patient_reference_tokens=patient_reference_tokens,
            )
        )

    render_summary_table(summaries)


def iter_ndjson_files(fhir_dir: Path) -> list[Path]:
    """Return all NDJSON files in deterministic filename order."""

    return sorted(path for path in fhir_dir.glob("*.ndjson") if path.is_file())


def derive_resource_type(input_path: Path) -> str:
    """Derive the resource type from a mixed-pattern NDJSON filename."""

    return input_path.name.split(".", maxsplit=1)[0]


def load_selected_patient_ids(patient_file: Path, n_patients: int, seed: int) -> set[str]:
    """Select the deterministic patient subset used by the sampler CLI."""

    # --- Section: Short-circuit invalid sample sizes ---
    if n_patients <= 0:
        return set()

    # --- Section: Collect patient ids before deterministic truncation ---
    patient_ids: list[str] = []
    for line in patient_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = load_json_object(line)
        patient_id = record.get("id")
        if isinstance(patient_id, str):
            patient_ids.append(patient_id)

    # --- Section: Return a seeded random subset ---
    rng = random.Random(seed)
    sample_size = min(n_patients, len(patient_ids))
    return set(rng.sample(sorted(patient_ids), sample_size))


def build_patient_reference_tokens(selected_patient_ids: set[str]) -> set[str]:
    """Build the raw reference tokens used for substring-based matching."""

    # Synthea references patients in both URN and ``Resource/id`` formats, so precomputing both
    # token shapes lets the downstream line filter stay simple and consistent.
    reference_tokens: set[str] = set()
    for patient_id in selected_patient_ids:
        reference_tokens.add(f"urn:uuid:{patient_id}")
        reference_tokens.add(f"Patient/{patient_id}")
    return reference_tokens


def line_matches_selected_patients(
    line: str,
    resource_type: str,
    selected_patient_ids: set[str],
    patient_reference_tokens: set[str],
) -> bool:
    """Return whether one raw NDJSON line belongs in the sampled subset."""

    # --- Section: Ignore blank lines ---
    if not line.strip():
        return False

    # --- Section: Parse Patient rows exactly ---
    if resource_type == "Patient":
        record = load_json_object(line)
        patient_id = record.get("id")
        return isinstance(patient_id, str) and patient_id in selected_patient_ids

    # --- Section: Match linked resources cheaply ---
    # For non-Patient files we intentionally use substring checks on the raw NDJSON line instead of
    # parsing every record, because the reference tokens are specific enough for this local sampler.
    return any(token in line for token in patient_reference_tokens)


def sample_one_file(
    input_path: Path,
    output_path: Path,
    resource_type: str,
    selected_patient_ids: set[str],
    patient_reference_tokens: set[str],
) -> SamplingSummaryRow:
    """Stream one NDJSON file into its sampled counterpart."""

    # --- Section: Initialize counters and destination ---
    records_in = 0
    records_kept = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Section: Stream matching lines to the output ---
    # Grouping both file handles in one ``with`` statement is the standard way to guarantee both
    # resources close cleanly even if sampling aborts partway through.
    with (
        input_path.open("r", encoding="utf-8") as source,
        output_path.open("w", encoding="utf-8") as target,
    ):
        for line in source:
            records_in += 1
            if not line_matches_selected_patients(
                line=line,
                resource_type=resource_type,
                selected_patient_ids=selected_patient_ids,
                patient_reference_tokens=patient_reference_tokens,
            ):
                continue
            target.write(line)
            records_kept += 1

    # --- Section: Return a summary row for reporting ---
    pct_kept = 0.0 if records_in == 0 else round((records_kept / records_in) * 100, 1)
    return SamplingSummaryRow(
        filename=input_path.name,
        records_in=records_in,
        records_kept=records_kept,
        pct_kept=pct_kept,
    )


def render_summary_table(summaries: list[SamplingSummaryRow]) -> None:
    """Print the sampler summary table to stdout."""

    click.echo("file\trecords-in\trecords-kept\t% kept")
    for summary in summaries:
        click.echo(
            f"{summary.filename}\t{summary.records_in}\t{summary.records_kept}\t{summary.pct_kept:.1f}%"
        )


def load_json_object(line: str) -> JsonObject:
    """Parse one NDJSON line into a JSON object."""

    parsed = json.loads(line)
    return cast(JsonObject, parsed)
