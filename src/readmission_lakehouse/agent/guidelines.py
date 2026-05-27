"""Evidence-based interventions for reducing 30-day readmissions.

Concise original summaries of well-established transitional-care practices. In
production these would be replaced by ingesting + chunking real guideline
documents (AHRQ, professional-society statements, etc.).
"""

GUIDELINES = [
    {
        "id": "g-med-rec",
        "title": "Medication reconciliation at discharge",
        "text": (
            "Reconcile the full medication list at discharge: compare pre-admission and "
            "discharge medications, resolve discrepancies, and explicitly counsel the "
            "patient on any new, changed, or stopped drugs. Pay particular attention to "
            "high-risk medications and polypharmacy, common drivers of post-discharge "
            "adverse events and readmission."
        ),
    },
    {
        "id": "g-followup",
        "title": "Timely outpatient follow-up",
        "text": (
            "Arrange a follow-up with a primary care provider or relevant specialist "
            "within 7 days of discharge, sooner for higher-risk patients. Booking the "
            "appointment before discharge, rather than leaving the patient to arrange it, "
            "markedly improves attendance and lowers early readmission."
        ),
    },
    {
        "id": "g-teachback",
        "title": "Teach-back patient education",
        "text": (
            "Use teach-back at discharge: ask the patient to restate, in their own words, "
            "their diagnosis, medication schedule, and the warning signs that should "
            "prompt them to seek care. Teach-back surfaces misunderstandings before the "
            "patient leaves and improves self-management."
        ),
    },
    {
        "id": "g-transition",
        "title": "Structured transitional care",
        "text": (
            "Assign a transition coach or discharge planner to coordinate the hospital-"
            "to-home handoff. Structured models such as the Transitional Care Model and "
            "Project RED — a dedicated coordinator, a clear after-hospital care plan, and "
            "follow-up — reduce 30-day readmissions."
        ),
    },
    {
        "id": "g-phone",
        "title": "Post-discharge follow-up contact",
        "text": (
            "Make a follow-up call or telehealth check-in within 48-72 hours of discharge "
            "to confirm the patient has their medications, understands the care plan, has "
            "follow-up scheduled, and has no warning symptoms. Early contact catches "
            "problems before they escalate to readmission."
        ),
    },
    {
        "id": "g-sdoh",
        "title": "Address social determinants of health",
        "text": (
            "Screen for social barriers that drive readmission: unstable housing, lack of "
            "transportation to follow-up, food insecurity, limited social support, and "
            "social isolation. Connect at-risk patients to community resources, social "
            "work, and home support — these often matter more than the diagnosis for "
            "whether a patient returns."
        ),
    },
    {
        "id": "g-hf",
        "title": "Heart failure self-management",
        "text": (
            "For heart-failure patients, reinforce daily weight monitoring, sodium and "
            "fluid guidance, and early recognition of worsening symptoms such as "
            "increasing breathlessness or swelling. A clear action plan for when to call "
            "a clinician helps prevent decompensation that leads to readmission."
        ),
    },
]
