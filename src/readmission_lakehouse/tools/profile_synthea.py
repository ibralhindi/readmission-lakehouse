"""Profile local Synthea FHIR NDJSON files and emit a Markdown summary.

This module gives the project a fast, local way to inspect resource coverage
before bronze and silver modeling decisions are locked in. It stays intentionally
lightweight by sampling NDJSON exports directly rather than requiring Spark just
to answer early shape and distribution questions.
"""

from __future__ import annotations

import json
import statistics
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast

import click
import structlog
from pydantic import BaseModel, ConfigDict, Field

# ``structlog`` keeps logs as structured key/value events, which makes CLI runs easier to filter
# in local development and later in orchestrated jobs.
LOGGER = structlog.get_logger(__name__)
# A shared frozen config keeps these report DTOs immutable once computed, which helps tests treat
# them as snapshot-like outputs instead of mutable working objects.
PROFILE_MODEL_CONFIG = ConfigDict(frozen=True)
DEFAULT_SAMPLE_SIZE = 1_000
BRONZED_RESOURCE_TYPES = frozenset(
    {
        "Patient",
        "Encounter",
        "Condition",
        "Procedure",
        "Organization",
        "Practitioner",
        "DocumentReference",
        "Observation",
        "MedicationRequest",
        "Immunization",
        "Claim",
        "AllergyIntolerance",
        "CarePlan",
        "CareTeam",
    }
)

JsonObject = dict[str, Any]


class SchemaFieldStat(BaseModel):
    """Presence statistics for one inferred JSON path."""

    model_config = PROFILE_MODEL_CONFIG

    path: str
    presence_pct: float


class EncounterStats(BaseModel):
    """Encounter-specific profile metrics."""

    model_config = PROFILE_MODEL_CONFIG

    class_distribution: dict[str, int] = Field(default_factory=dict)
    status_distribution: dict[str, int] = Field(default_factory=dict)
    period_start_min: str | None = None
    period_start_max: str | None = None
    period_start_median: str | None = None
    period_end_min: str | None = None
    period_end_max: str | None = None
    period_end_median: str | None = None


class ConditionCodeStat(BaseModel):
    """Frequency summary for one Condition code."""

    model_config = PROFILE_MODEL_CONFIG

    code: str | None = None
    display: str | None = None
    frequency: int


class PatientStats(BaseModel):
    """Patient-specific profile metrics."""

    model_config = PROFILE_MODEL_CONFIG

    gender_distribution: dict[str, int] = Field(default_factory=dict)
    birth_year_decades: dict[str, int] = Field(default_factory=dict)
    deceased_pct: float | None = None


class ResourceSection(BaseModel):
    """Rendered content for one resource section."""

    model_config = PROFILE_MODEL_CONFIG

    resource_type: str
    source_filename: str
    total_records: int
    bronze_plan: str
    sample_size: int
    schema_fields: list[SchemaFieldStat] = Field(default_factory=list)
    encounter_stats: EncounterStats | None = None
    condition_code_stats: list[ConditionCodeStat] = Field(default_factory=list)
    patient_stats: PatientStats | None = None


class ProfileReport(BaseModel):
    """Top-level Markdown report DTO."""

    model_config = PROFILE_MODEL_CONFIG

    sections: list[ResourceSection] = Field(default_factory=list)


# Click turns this function into a small CLI without changing the Python call signature, so the
# rest of the module can still test the pure helpers directly.
@click.command()
@click.option(
    "--fhir-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=str),
    required=True,
    help="Directory containing Synthea FHIR NDJSON files.",
)
@click.option(
    "--output-md",
    type=click.Path(file_okay=True, dir_okay=False, path_type=str),
    required=True,
    help="Markdown path to write the profile summary to.",
)
def cli(fhir_dir: str, output_md: str) -> None:
    """Build a Markdown profile for local Synthea FHIR exports."""

    # --- Section: Normalize CLI paths ---
    fhir_dir_path = Path(fhir_dir)
    output_md_path = Path(output_md)

    # --- Section: Build and persist the report ---
    LOGGER.info(
        "profiling_synthea_fhir",
        fhir_dir=str(fhir_dir_path),
        output_md=str(output_md_path),
    )
    report = build_report(fhir_dir=fhir_dir_path)
    write_markdown(report=report, output_md=output_md_path)


def build_report(fhir_dir: Path) -> ProfileReport:
    """Build report sections for all NDJSON resources in a directory."""

    # --- Section: Accumulate one section per resource file ---
    sections: list[ResourceSection] = []
    for input_path in iter_ndjson_files(fhir_dir):
        resource_type = derive_resource_type(input_path)
        total_records = count_records(input_path)
        sample_records = load_sample_records(input_path, sample_size=DEFAULT_SAMPLE_SIZE)
        section = ResourceSection(
            resource_type=resource_type,
            source_filename=input_path.name,
            total_records=total_records,
            bronze_plan=bronze_plan_for(resource_type),
            sample_size=len(sample_records),
            schema_fields=infer_schema_fields(sample_records),
            encounter_stats=build_encounter_stats_safe(resource_type, sample_records),
            condition_code_stats=build_condition_stats_safe(resource_type, sample_records),
            patient_stats=build_patient_stats_safe(resource_type, sample_records),
        )
        sections.append(section)
    return ProfileReport(sections=sections)


def iter_ndjson_files(fhir_dir: Path) -> list[Path]:
    """Return all NDJSON files in deterministic filename order."""

    return sorted(path for path in fhir_dir.glob("*.ndjson") if path.is_file())


def derive_resource_type(input_path: Path) -> str:
    """Derive the FHIR resource type from a mixed-pattern NDJSON filename."""

    return input_path.name.split(".", maxsplit=1)[0]


def bronze_plan_for(resource_type: str) -> str:
    """Return the bronze-plan tag for a resource type."""

    return "bronzed" if resource_type in BRONZED_RESOURCE_TYPES else "available-not-bronzed"


def count_records(input_path: Path) -> int:
    """Count newline-delimited JSON records in one file."""

    with input_path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def load_sample_records(input_path: Path, sample_size: int) -> list[JsonObject]:
    """Load up to ``sample_size`` NDJSON objects from the top of a file."""

    # --- Section: Read a bounded prefix of the file ---
    sample_records: list[JsonObject] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if index >= sample_size:
                break
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                sample_records.append(cast(JsonObject, parsed))
    return sample_records


def infer_schema_fields(records: list[JsonObject]) -> list[SchemaFieldStat]:
    """Infer flat dotted-path field presence over a sample of JSON records."""

    # --- Section: Short-circuit empty samples ---
    if not records:
        return []

    # --- Section: Count non-null path occurrences ---
    presence_counter: Counter[str] = Counter()
    for record in records:
        for path in collect_non_null_paths(record):
            presence_counter[path] += 1

    # --- Section: Convert counts to percentages ---
    total_records = len(records)
    return [
        SchemaFieldStat(path=path, presence_pct=round((count / total_records) * 100, 1))
        for path, count in sorted(presence_counter.items())
    ]


def collect_non_null_paths(value: object, prefix: str = "") -> set[str]:
    """Collect dotted JSON paths whose values are populated in one record."""

    # --- Section: Stop on absent values ---
    paths: set[str] = set()
    if value is None:
        return paths

    # --- Section: Recurse through objects ---
    if isinstance(value, dict):
        for key, nested_value in value.items():
            current_path = f"{prefix}.{key}" if prefix else str(key)
            if nested_value is None:
                continue
            paths.add(current_path)
            paths.update(collect_non_null_paths(nested_value, current_path))
        return paths

    # --- Section: Recurse through arrays ---
    if isinstance(value, list):
        if prefix:
            paths.add(prefix)
        # ``[]`` marks "some element exists here" without pretending every list item has a stable
        # numeric position, which would make cross-record schema summaries noisy.
        item_prefix = f"{prefix}[]" if prefix else "[]"
        for item in value:
            if item is None:
                continue
            paths.add(item_prefix)
            paths.update(collect_non_null_paths(item, item_prefix))
        return paths

    # --- Section: Record scalar leaf values ---
    if prefix:
        paths.add(prefix)
    return paths


def build_encounter_stats_safe(
    resource_type: str, sample_records: list[JsonObject]
) -> EncounterStats | None:
    """Return Encounter stats when implemented and relevant."""

    if resource_type != "Encounter":
        return None

    return build_encounter_stats(sample_records)


def build_condition_stats_safe(
    resource_type: str, sample_records: list[JsonObject]
) -> list[ConditionCodeStat]:
    """Return Condition code stats when implemented and relevant."""

    if resource_type != "Condition":
        return []

    return build_condition_code_stats(sample_records)


def build_patient_stats_safe(
    resource_type: str,
    sample_records: list[JsonObject],
) -> PatientStats | None:
    """Return Patient stats when implemented and relevant."""

    if resource_type != "Patient":
        return None

    return build_patient_stats(sample_records)


def parse_iso_datetime(value: object) -> datetime | None:
    """Parse a FHIR datetime string into an aware UTC datetime."""

    if not isinstance(value, str) or not value:
        return None

    # FHIR exports often use the ``Z`` suffix for UTC, but normalizing to an explicit offset keeps
    # the parser behavior consistent across ISO-8601 variants.
    normalized_value = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed_value = datetime.fromisoformat(normalized_value)
    except ValueError:
        return None

    if parsed_value.tzinfo is None:
        return parsed_value.replace(tzinfo=UTC)
    return parsed_value.astimezone(UTC)


def format_datetime(value: datetime | None) -> str | None:
    """Format a datetime as an ISO-8601 string."""

    if value is None:
        return None
    return value.isoformat().replace("+00:00", "Z")


def summarize_datetimes(values: list[datetime]) -> tuple[str | None, str | None, str | None]:
    """Return min, max, and median strings for a datetime list."""

    # --- Section: Short-circuit empty inputs ---
    if not values:
        return None, None, None

    # --- Section: Choose a calendar midpoint ---
    sorted_values = sorted(values)
    middle_index = len(sorted_values) // 2
    if len(sorted_values) % 2 == 1:
        median_value = sorted_values[middle_index]
    else:
        lower_value = sorted_values[middle_index - 1]
        upper_value = sorted_values[middle_index]
        # ``statistics.median`` works on numeric timestamps, so converting to epoch seconds gives a
        # true midpoint instead of picking one of the two central datetimes arbitrarily.
        median_timestamp = statistics.median([lower_value.timestamp(), upper_value.timestamp()])
        median_value = datetime.fromtimestamp(median_timestamp, tz=UTC)

    return (
        format_datetime(sorted_values[0]),
        format_datetime(sorted_values[-1]),
        format_datetime(median_value),
    )


def extract_first_coding(record: JsonObject) -> JsonObject | None:
    """Return the first coding object from a FHIR CodeableConcept-like dict."""

    code_value = record.get("code")
    if not isinstance(code_value, dict):
        return None

    coding_value = code_value.get("coding")
    if not isinstance(coding_value, list) or not coding_value:
        return None

    first_coding = coding_value[0]
    if not isinstance(first_coding, dict):
        return None
    return cast(JsonObject, first_coding)


def birth_year_to_decade_label(value: object) -> str | None:
    """Convert a birthDate value into a decade label like ``1970s``."""

    if not isinstance(value, str) or not value:
        return None

    try:
        birth_date = date.fromisoformat(value)
    except ValueError:
        return None

    decade_start = (birth_date.year // 10) * 10
    return f"{decade_start}s"


def build_encounter_stats(sample_records: list[JsonObject]) -> EncounterStats:
    """Build Encounter class, status, and period summary statistics."""

    # --- Section: Accumulate distributions and period values ---
    class_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    period_starts: list[datetime] = []
    period_ends: list[datetime] = []

    for record in sample_records:
        class_value = record.get("class")
        if isinstance(class_value, dict):
            class_code = class_value.get("code")
            if isinstance(class_code, str):
                class_counter[class_code] += 1

        status_value = record.get("status")
        if isinstance(status_value, str):
            status_counter[status_value] += 1

        period_value = record.get("period")
        if not isinstance(period_value, dict):
            continue

        period_start = parse_iso_datetime(period_value.get("start"))
        if period_start is not None:
            period_starts.append(period_start)

        period_end = parse_iso_datetime(period_value.get("end"))
        if period_end is not None:
            period_ends.append(period_end)

    # --- Section: Collapse raw observations into summary fields ---
    period_start_min, period_start_max, period_start_median = summarize_datetimes(period_starts)
    period_end_min, period_end_max, period_end_median = summarize_datetimes(period_ends)

    return EncounterStats(
        class_distribution=dict(class_counter),
        status_distribution=dict(status_counter),
        period_start_min=period_start_min,
        period_start_max=period_start_max,
        period_start_median=period_start_median,
        period_end_min=period_end_min,
        period_end_max=period_end_max,
        period_end_median=period_end_median,
    )


def build_condition_code_stats(sample_records: list[JsonObject]) -> list[ConditionCodeStat]:
    """Build the top Condition code frequency table for one sample."""

    # --- Section: Count codes while keeping one human-readable label ---
    code_counter: Counter[str] = Counter()
    display_by_code: dict[str, str | None] = {}

    for record in sample_records:
        first_coding = extract_first_coding(record)
        if first_coding is None:
            continue

        code = first_coding.get("code")
        if not isinstance(code, str) or not code:
            continue

        display_value = first_coding.get("display")
        display = display_value if isinstance(display_value, str) else None
        code_counter[code] += 1
        if code not in display_by_code or display_by_code[code] is None:
            display_by_code[code] = display

    # --- Section: Return the most common codes only ---
    return [
        ConditionCodeStat(code=code, display=display_by_code.get(code), frequency=frequency)
        for code, frequency in code_counter.most_common(10)
    ]


def build_patient_stats(sample_records: list[JsonObject]) -> PatientStats:
    """Build gender, birth-decade, and deceased-percentage summary statistics."""

    # --- Section: Accumulate patient-level signals ---
    gender_counter: Counter[str] = Counter()
    birth_year_counter: Counter[str] = Counter()
    deceased_count = 0

    for record in sample_records:
        gender_value = record.get("gender")
        if isinstance(gender_value, str):
            gender_counter[gender_value] += 1

        birth_year = birth_year_to_decade_label(record.get("birthDate"))
        if birth_year is not None:
            birth_year_counter[birth_year] += 1

        if record.get("deceasedDateTime") is not None:
            deceased_count += 1

    # --- Section: Convert counts to report-friendly metrics ---
    deceased_pct = None
    if sample_records:
        deceased_pct = round((deceased_count / len(sample_records)) * 100, 1)

    return PatientStats(
        gender_distribution=dict(gender_counter),
        birth_year_decades=dict(birth_year_counter),
        deceased_pct=deceased_pct,
    )


def write_markdown(report: ProfileReport, output_md: Path) -> None:
    """Render a profile report to Markdown on disk."""

    # --- Section: Render the full document in memory ---
    lines: list[str] = ["# Synthea FHIR Profile", ""]
    for section in report.sections:
        lines.extend(render_section(section))

    # --- Section: Persist to disk ---
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def render_section(section: ResourceSection) -> list[str]:
    """Render one resource section as Markdown lines."""

    # --- Section: Build the shared section header ---
    lines = [
        f"## {section.resource_type}",
        f"**Bronze plan**: {section.bronze_plan}",
        "",
        f"- Source file: `{section.source_filename}`",
        f"- Total records: {section.total_records}",
        f"- Sample size: {section.sample_size}",
        "",
        "### Schema Presence",
    ]

    # --- Section: Render schema coverage lines ---
    if section.schema_fields:
        for field_stat in section.schema_fields:
            lines.append(f"- `{field_stat.path}`: {field_stat.presence_pct:.1f}%")
    else:
        lines.append("- No sample records available.")

    # --- Section: Append resource-specific detail blocks ---
    if section.resource_type == "Encounter":
        lines.extend(render_encounter_section(section.encounter_stats))
    if section.resource_type == "Condition":
        lines.extend(render_condition_section(section.condition_code_stats))
    if section.resource_type == "Patient":
        lines.extend(render_patient_section(section.patient_stats))

    lines.append("")
    return lines


def render_encounter_section(stats: EncounterStats | None) -> list[str]:
    """Render Encounter-only Markdown lines."""

    # --- Section: Render the subsection header ---
    lines = ["", "### Encounter Stats"]
    if stats is None:
        lines.append("- No Encounter stats available.")
        return lines

    # --- Section: Render distributions and date summaries ---
    lines.append("- Class distribution:")
    for key, value in sorted(stats.class_distribution.items()):
        lines.append(f"  - {key}: {value}")
    lines.append("- Status distribution:")
    for key, value in sorted(stats.status_distribution.items()):
        lines.append(f"  - {key}: {value}")
    lines.append(f"- Period start min: {stats.period_start_min}")
    lines.append(f"- Period start max: {stats.period_start_max}")
    lines.append(f"- Period start median: {stats.period_start_median}")
    lines.append(f"- Period end min: {stats.period_end_min}")
    lines.append(f"- Period end max: {stats.period_end_max}")
    lines.append(f"- Period end median: {stats.period_end_median}")
    return lines


def render_condition_section(stats: list[ConditionCodeStat]) -> list[str]:
    """Render Condition-only Markdown lines."""

    lines = ["", "### Condition Stats"]
    if not stats:
        lines.append("- No Condition stats available.")
        return lines

    for item in stats:
        lines.append(f"- `{item.code}` ({item.display or 'unknown'}): {item.frequency}")
    return lines


def render_patient_section(stats: PatientStats | None) -> list[str]:
    """Render Patient-only Markdown lines."""

    # --- Section: Render the subsection header ---
    lines = ["", "### Patient Stats"]
    if stats is None:
        lines.append("- No Patient stats available.")
        return lines

    # --- Section: Render demographic summaries ---
    lines.append("- Gender distribution:")
    for key, value in sorted(stats.gender_distribution.items()):
        lines.append(f"  - {key}: {value}")
    lines.append("- Birth year decades:")
    for key, value in sorted(stats.birth_year_decades.items()):
        lines.append(f"  - {key}: {value}")
    if stats.deceased_pct is None:
        lines.append("- Deceased percentage: n/a")
    else:
        lines.append(f"- Deceased percentage: {stats.deceased_pct:.1f}%")
    return lines
