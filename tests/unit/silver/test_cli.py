"""Tests for the silver validation CLI guards.

These cover the failure paths that real data can't exercise: the Synthea
dataset quarantines zero rows, so without these the threshold and
empty-source guards would never be proven to fire.

Spark is mocked out entirely — nothing here needs a session.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

import pytest

from readmission_lakehouse.silver import cli

# Fixture returns a callable that accepts a result dict plus optional CLI flags.
RunCli = Callable[..., None]


def _result(source: int, valid: int, quarantine: int) -> dict[str, Any]:
    """Build a ValidationResult-shaped dict."""
    return {
        "bronze_table": "rl_dev.bronze.patient",
        "valid_table": "rl_dev.silver.patient_valid",
        "quarantine_table": "rl_dev.silver.patient_quarantine",
        "source_rows": source,
        "valid_rows": valid,
        "quarantine_rows": quarantine,
    }


@pytest.fixture
def run_cli(monkeypatch: pytest.MonkeyPatch) -> RunCli:
    """Run cli.main() with Spark stubbed and a fixed validation result.

    Returns a callable: run_cli(result_dict, *extra_cli_args)
    """

    def _run(result: dict[str, Any], *extra_args: str) -> None:
        # Never build a real SparkSession.
        monkeypatch.setattr(
            cli.SparkSession,
            "builder",
            type("B", (), {"getOrCreate": staticmethod(lambda: None)})(),
        )
        # Never touch a warehouse. Underscore prefix: stub ignores all kwargs (ruff ARG005).
        monkeypatch.setattr(cli, "validate_resource", lambda **_kwargs: result)
        monkeypatch.setattr(
            sys, "argv", ["rl-silver-validate", "--resource-name", "Patient", *extra_args]
        )
        cli.main()

    return _run


# --------------------------------------------------------------------------
# Quarantine-rate threshold
# --------------------------------------------------------------------------


def test_exits_when_quarantine_rate_exceeds_threshold(run_cli: RunCli) -> None:
    """10% quarantined against a 1% threshold must fail the job."""
    with pytest.raises(SystemExit) as exc:
        run_cli(_result(source=100, valid=90, quarantine=10), "--max-quarantine-rate", "0.01")
    assert exc.value.code == 1


def test_passes_when_quarantine_rate_within_threshold(run_cli: RunCli) -> None:
    """0.5% quarantined against a 1% threshold must succeed."""
    run_cli(_result(source=1000, valid=995, quarantine=5), "--max-quarantine-rate", "0.01")


def test_passes_when_rate_exactly_equals_threshold(run_cli: RunCli) -> None:
    """The check is strictly greater-than: exactly at the threshold passes.

    Pinned deliberately — this is the kind of boundary that silently flips
    if someone changes > to >=.
    """
    run_cli(_result(source=100, valid=99, quarantine=1), "--max-quarantine-rate", "0.01")


def test_passes_when_nothing_quarantined(run_cli: RunCli) -> None:
    """The current real-world case: Synthea data quarantines zero rows."""
    run_cli(_result(source=11423, valid=11423, quarantine=0))


# --------------------------------------------------------------------------
# Empty source
# --------------------------------------------------------------------------


def test_exits_when_source_is_empty(run_cli: RunCli) -> None:
    """An empty bronze table means upstream ingestion failed, not that
    validation succeeded. A clean run over zero rows is the most dangerous
    outcome, so it must fail loudly."""
    with pytest.raises(SystemExit) as exc:
        run_cli(_result(source=0, valid=0, quarantine=0))
    assert exc.value.code == 1


def test_empty_source_permitted_with_flag(run_cli: RunCli) -> None:
    """--allow-empty-source must not divide by zero when computing the rate."""
    run_cli(_result(source=0, valid=0, quarantine=0), "--allow-empty-source")


# --------------------------------------------------------------------------
# Argument handling
# --------------------------------------------------------------------------


def test_default_threshold_is_one_percent(run_cli: RunCli) -> None:
    """2% quarantined must fail on defaults, with no --max-quarantine-rate passed."""
    with pytest.raises(SystemExit) as exc:
        run_cli(_result(source=100, valid=98, quarantine=2))
    assert exc.value.code == 1
