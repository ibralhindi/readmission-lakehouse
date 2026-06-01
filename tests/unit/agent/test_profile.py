"""Unit tests for patient profile request validation."""

from __future__ import annotations

import pytest

from readmission_lakehouse.agent import profile


@pytest.mark.parametrize("patient_id", ["not-a-uuid", "1; DROP TABLE patients"])
def test_get_patient_profile_rejects_invalid_uuid_before_query(
    monkeypatch: pytest.MonkeyPatch,
    patient_id: str,
) -> None:
    """Invalid patient ids fail before any warehouse query can run."""

    def fail_query(_sql_text: str) -> list[dict]:
        raise AssertionError("db.query should not be called for invalid patient_id")

    monkeypatch.setattr(profile.db, "query", fail_query)

    with pytest.raises(ValueError, match="expected a UUID string"):
        profile.get_patient_profile(patient_id)


def test_get_patient_profile_normalizes_valid_uuid_before_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid UUIDs are canonicalized before being interpolated into SQL."""
    raw_patient_id = "E305DACA-DDAA-4446-A3F4-5C89DF23A17C"
    expected_patient_id = "e305daca-ddaa-4446-a3f4-5c89df23a17c"
    captured_sql: list[str] = []
    fake_row = {"patient_id": expected_patient_id}

    def fake_query(sql_text: str) -> list[dict]:
        captured_sql.append(sql_text)
        return [fake_row]

    monkeypatch.setattr(profile.db, "query", fake_query)

    result = profile.get_patient_profile(raw_patient_id)

    assert result == fake_row
    assert len(captured_sql) == 1
    assert f"WHERE dp.patient_id = '{expected_patient_id}'" in captured_sql[0]
    assert raw_patient_id not in captured_sql[0]
