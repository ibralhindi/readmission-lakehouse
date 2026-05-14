"""Sampler CLI tests for local Synthea NDJSON exports.

These checks protect the development sampler that trims Synthea down to a
patient subset while keeping related resource files aligned.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from readmission_lakehouse.tools import sample_synthea


def write_ndjson(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(record) for record in records).rstrip() + "\n",
        encoding="utf-8",
    )


def read_ndjson(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def test_sample_cli_keeps_only_selected_patient_resources_and_preserves_filenames(
    tmp_path: Path,
) -> None:
    # --- Section: Arrange a tiny multi-file FHIR export ---
    fhir_dir = tmp_path / "fhir"
    out_dir = tmp_path / "sampled"
    fhir_dir.mkdir()

    write_ndjson(
        fhir_dir / "Patient.ndjson",
        [
            {"id": "patient-001", "gender": "female"},
            {"id": "patient-002", "gender": "male"},
        ],
    )
    write_ndjson(
        fhir_dir / "Encounter.ndjson",
        [
            {"id": "encounter-001", "subject": {"reference": "Patient/patient-001"}},
            {"id": "encounter-002", "subject": {"reference": "Patient/patient-002"}},
        ],
    )
    write_ndjson(
        fhir_dir / "Observation.1778542031678.ndjson",
        [
            {"id": "observation-001", "subject": {"reference": "urn:uuid:patient-001"}},
            {"id": "observation-002", "subject": {"reference": "urn:uuid:patient-002"}},
        ],
    )
    (fhir_dir / "parameters.json").write_text('{"ignored": true}\n', encoding="utf-8")

    # --- Section: Run the sampler CLI ---
    runner = CliRunner()
    result = runner.invoke(
        sample_synthea.cli,
        [
            "--fhir-dir",
            str(fhir_dir),
            "--out-dir",
            str(out_dir),
            "--n-patients",
            "1",
            "--seed",
            "42",
        ],
    )

    assert result.exit_code == 0

    # --- Section: Assert only linked records were kept ---
    patient_records = read_ndjson(out_dir / "Patient.ndjson")
    encounter_records = read_ndjson(out_dir / "Encounter.ndjson")
    observation_records = read_ndjson(out_dir / "Observation.1778542031678.ndjson")

    assert [record["id"] for record in patient_records] == ["patient-001"]
    assert [record["id"] for record in encounter_records] == ["encounter-001"]
    assert [record["id"] for record in observation_records] == ["observation-001"]
    assert not (out_dir / "parameters.json").exists()

    # --- Section: Assert the summary output stays user-friendly ---
    assert "Patient.ndjson\t2\t1\t50.0%" in result.output
    assert "Encounter.ndjson\t2\t1\t50.0%" in result.output
    assert "Observation.1778542031678.ndjson\t2\t1\t50.0%" in result.output
