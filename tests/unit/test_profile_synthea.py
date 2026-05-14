"""Profiler CLI tests for local Synthea NDJSON exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from readmission_lakehouse.tools.profile_synthea import (
    build_condition_code_stats,
    build_encounter_stats,
    build_patient_stats,
    cli,
)

EXPECTED_BRONZED_SECTION_COUNT = 3
EXPECTED_TOP_CONDITION_FREQUENCY = 2
EXPECTED_PATIENT_DECEASED_PCT = 25.0


def write_ndjson(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(record) for record in records).rstrip() + "\n",
        encoding="utf-8",
    )


def test_profile_cli_writes_headings_bronze_tags_and_expected_stat_sections(
    tmp_path: Path,
) -> None:
    fhir_dir = tmp_path / "fhir"
    fhir_dir.mkdir()
    output_md = tmp_path / "profile.md"

    write_ndjson(
        fhir_dir / "Patient.ndjson",
        [
            {
                "id": "patient-001",
                "gender": "female",
                "birthDate": "1982-01-01",
                "deceasedDateTime": None,
            },
            {
                "id": "patient-002",
                "gender": "male",
                "birthDate": "1974-05-02",
                "deceasedDateTime": "2024-01-01T00:00:00Z",
            },
            {
                "id": "patient-003",
                "gender": "male",
                "birthDate": "1978-09-10",
                "deceasedDateTime": None,
            },
        ],
    )
    write_ndjson(
        fhir_dir / "Encounter.ndjson",
        [
            {
                "id": "encounter-001",
                "status": "finished",
                "class": {"code": "AMB"},
                "subject": {"reference": "urn:uuid:patient-001"},
                "period": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-02T00:00:00Z",
                },
            },
            {
                "id": "encounter-002",
                "status": "finished",
                "class": {"code": "AMB"},
                "subject": {"reference": "urn:uuid:patient-002"},
                "period": {
                    "start": "2024-02-01T00:00:00Z",
                    "end": "2024-02-03T00:00:00Z",
                },
            },
            {
                "id": "encounter-003",
                "status": "in-progress",
                "class": {"code": "IMP"},
                "subject": {"reference": "urn:uuid:patient-003"},
                "period": {
                    "start": "2024-03-01T00:00:00Z",
                    "end": "2024-03-04T00:00:00Z",
                },
            },
        ],
    )
    write_ndjson(
        fhir_dir / "Condition.ndjson",
        [
            {
                "id": "condition-001",
                "code": {
                    "coding": [{"code": "40055000", "display": "Chronic sinusitis (disorder)"}]
                },
            },
            {
                "id": "condition-002",
                "code": {
                    "coding": [{"code": "40055000", "display": "Chronic sinusitis (disorder)"}]
                },
            },
            {
                "id": "condition-003",
                "code": {"coding": [{"code": "224299000", "display": "Received higher education"}]},
            },
        ],
    )
    write_ndjson(
        fhir_dir / "SupplyDelivery.1778542031678.ndjson",
        [
            {
                "id": "supply-001",
                "patient": {"reference": "urn:uuid:patient-001"},
                "status": "completed",
            }
        ],
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--fhir-dir",
            str(fhir_dir),
            "--output-md",
            str(output_md),
        ],
    )

    assert result.exit_code == 0

    markdown = output_md.read_text(encoding="utf-8")

    assert "## Patient" in markdown
    assert "## Encounter" in markdown
    assert "## SupplyDelivery" in markdown
    assert markdown.count("**Bronze plan**: bronzed") == EXPECTED_BRONZED_SECTION_COUNT
    assert "**Bronze plan**: available-not-bronzed" in markdown

    assert "female: 1" in markdown
    assert "male: 2" in markdown
    assert "1970s: 2" in markdown
    assert "Deceased percentage: 33.3%" in markdown
    assert "AMB: 2" in markdown
    assert "IMP: 1" in markdown
    assert "finished: 2" in markdown
    assert "in-progress: 1" in markdown
    assert "`40055000` (Chronic sinusitis (disorder)): 2" in markdown


def test_build_encounter_stats_handles_missing_and_malformed_period_values() -> None:
    stats = build_encounter_stats(
        [
            {
                "class": {"code": "AMB"},
                "status": "finished",
                "period": {"start": "2024-01-01T00:00:00Z", "end": "2024-01-02T00:00:00Z"},
            },
            {
                "class": {"code": "IMP"},
                "status": "in-progress",
                "period": {"start": "not-a-date", "end": None},
            },
            {
                "class": {"code": "AMB"},
                "status": "finished",
                "period": {"start": "2024-01-03T00:00:00Z", "end": "2024-01-04T00:00:00Z"},
            },
        ]
    )

    assert stats.class_distribution == {"AMB": 2, "IMP": 1}
    assert stats.status_distribution == {"finished": 2, "in-progress": 1}
    assert stats.period_start_min == "2024-01-01T00:00:00Z"
    assert stats.period_start_max == "2024-01-03T00:00:00Z"
    assert stats.period_start_median == "2024-01-02T00:00:00Z"
    assert stats.period_end_min == "2024-01-02T00:00:00Z"
    assert stats.period_end_max == "2024-01-04T00:00:00Z"
    assert stats.period_end_median == "2024-01-03T00:00:00Z"


def test_build_condition_code_stats_preserves_code_display_pairing() -> None:
    stats = build_condition_code_stats(
        [
            {"code": {"coding": [{"code": "40055000", "display": "Chronic sinusitis (disorder)"}]}},
            {"code": {"coding": [{"code": "40055000", "display": "Chronic sinusitis (disorder)"}]}},
            {"code": {"coding": [{"code": "224299000", "display": "Received higher education"}]}},
            {"code": {"coding": []}},
        ]
    )

    assert stats[0].code == "40055000"
    assert stats[0].display == "Chronic sinusitis (disorder)"
    assert stats[0].frequency == EXPECTED_TOP_CONDITION_FREQUENCY
    assert stats[1].code == "224299000"
    assert stats[1].display == "Received higher education"
    assert stats[1].frequency == 1


def test_build_patient_stats_buckets_decades_and_skips_bad_birth_dates() -> None:
    stats = build_patient_stats(
        [
            {"gender": "female", "birthDate": "1982-01-01", "deceasedDateTime": None},
            {
                "gender": "male",
                "birthDate": "1974-05-02",
                "deceasedDateTime": "2024-01-01T00:00:00Z",
            },
            {"gender": "male", "birthDate": "1978-09-10", "deceasedDateTime": None},
            {"gender": "unknown", "birthDate": "not-a-date", "deceasedDateTime": None},
        ]
    )

    assert stats.gender_distribution == {"female": 1, "male": 2, "unknown": 1}
    assert stats.birth_year_decades == {"1970s": 2, "1980s": 1}
    assert stats.deceased_pct == EXPECTED_PATIENT_DECEASED_PCT
