"""Structured patient profile from the gold star schema (via the SQL warehouse).

Pulls the facts a care manager needs: demographics, the latest inpatient index
admission, length of stay, and the 30-day readmission outcome. Comorbidities are
deliberately NOT here — the gold star has no patient↔condition fact, and the
patient's conditions live in their clinical notes, retrieved via RAG.
"""

from __future__ import annotations

from readmission_lakehouse.agent import db


def list_cohort_patients(n_patients: int = 150) -> list[dict]:
    """The same ~150 IMP-cohort patients whose notes are embedded — identical
    `ORDER BY patient_id LIMIT`, so the UI roster never offers a patient we have
    no notes for."""
    sql = f"""
        SELECT
            dp.patient_id,
            MAX(dp.gender) AS gender,
            MAX(FLOOR(DATEDIFF(current_date(), CAST(dp.birth_date AS DATE)) / 365.25)) AS age,
            MAX(CASE WHEN fr.was_readmitted_30d_excl_transfers THEN 1 ELSE 0 END) AS ever_readmitted
        FROM rl_dev.gold.fact_readmission fr
        JOIN rl_dev.gold.dim_patient dp ON fr.patient_key = dp.patient_key
        GROUP BY dp.patient_id
        ORDER BY dp.patient_id
        LIMIT {int(n_patients)}
    """
    return db.query(sql)


def get_patient_profile(patient_id: str) -> dict:
    """Latest IMP index admission + demographics + readmission outcome for one
    patient. patient_id comes from list_cohort_patients (a controlled UUID), so
    the f-string is safe here; production would bind it as a query parameter."""
    sql = f"""
        SELECT
            dp.patient_id,
            dp.gender,
            dp.race_display,
            dp.ethnicity_display,
            dp.marital_status_code,
            FLOOR(DATEDIFF(d_adm.full_date, CAST(dp.birth_date AS DATE)) / 365.25) AS age_at_admission,
            fe.encounter_class_code,
            CAST(d_adm.full_date AS STRING) AS index_admission_date,
            CAST(d_dis.full_date AS STRING) AS index_discharge_date,
            ROUND(fe.length_of_stay_hours / 24.0, 1) AS length_of_stay_days,
            fr.days_to_readmission,
            fr.was_readmitted_30d,
            fr.is_likely_transfer,
            fr.was_readmitted_30d_excl_transfers,
            MAX(fr.was_readmitted_30d_excl_transfers)
                OVER (PARTITION BY dp.patient_id) AS ever_readmitted_30d
        FROM rl_dev.gold.fact_readmission fr
        JOIN rl_dev.gold.fact_encounter fe ON fr.index_encounter_key = fe.encounter_key
        JOIN rl_dev.gold.dim_patient dp ON fr.patient_key = dp.patient_key
        LEFT JOIN rl_dev.gold.dim_date d_adm ON fr.index_admission_date_key = d_adm.date_key
        LEFT JOIN rl_dev.gold.dim_date d_dis ON fr.index_discharge_date_key = d_dis.date_key
        WHERE dp.patient_id = '{patient_id}'
        ORDER BY d_adm.full_date DESC
        LIMIT 1
    """  # noqa: E501
    rows = db.query(sql)
    return rows[0] if rows else {}


if __name__ == "__main__":
    patients = list_cohort_patients()
    print(f"Cohort: {len(patients)} patients. First 3:")
    for p in patients[:3]:
        print(" ", p)

    sample_id = patients[0]["patient_id"]
    print(f"\nProfile for {sample_id}:")
    for k, v in get_patient_profile(sample_id).items():
        print(f"  {k}: {v}")
