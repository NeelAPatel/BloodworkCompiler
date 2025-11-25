from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

from app.models import ContinuousResultsTable, LabRow, PatientBundle, ReferenceRange
from pydantic import ValidationError


@dataclass
class ParserOptions:
    source: str = "unknown"
    patient_id: Optional[str] = None


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Basic text extractor that works with plain-text fixtures.

    If the content cannot be decoded to UTF-8 or is mostly non-printable, an empty string
    is returned so that the caller can fall back to OCR.
    """

    try:
        text = pdf_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""

    printable = sum(1 for ch in text if ch.isprintable())
    if len(text) == 0:
        return ""
    if printable / len(text) < 0.6:
        return ""
    return text


def parse_text_rows(text: str, source: str, patient_id: Optional[str] = None) -> PatientBundle:
    rows: List[LabRow] = []
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#"):
            continue
        parsed = _parse_line(cleaned, source)
        if parsed:
            rows.append(parsed)

    return PatientBundle(patient_id=patient_id, rows=rows, source=source)


def _parse_line(line: str, source: str) -> Optional[LabRow]:
    # CSV-like structure: name,value,unit,range
    parts = [segment.strip() for segment in line.split(",") if segment.strip()]
    if len(parts) >= 2:
        name = parts[0]
        value = float(parts[1])
        unit = parts[2] if len(parts) >= 3 else None
        ref_range = None
        if len(parts) >= 4 and "-" in parts[3]:
            lower_str, upper_str = [p.strip() for p in parts[3].split("-", maxsplit=1)]
            lower = float(lower_str) if lower_str else None
            upper = float(upper_str) if upper_str else None
            ref_range = ReferenceRange(lower=lower, upper=upper)
        normalized = name.lower()
        known_metric = normalized in LabRow.EXPECTED_RANGES
        return LabRow(
            raw_name=name,
            normalized_name=normalized,
            value=value,
            unit=unit,
            reference_range=ref_range,
            source=source,
            known_metric=known_metric,
        )

    # Pattern: "Name: value unit (lower-upper)"
    match = re.match(
        r"(?P<name>[A-Za-z0-9 /%+-]+):\s*(?P<value>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z/%]+)?(?:\s*\((?P<lower>-?\d+(?:\.\d+)?)\s*-\s*(?P<upper>-?\d+(?:\.\d+)?)\))?",
        line,
    )
    if match:
        name = match.group("name")
        value = float(match.group("value"))
        unit = match.group("unit")
        ref_range = None
        if match.group("lower"):
            ref_range = ReferenceRange(
                lower=float(match.group("lower")), upper=float(match.group("upper"))
            )
        normalized = name.lower()
        known_metric = normalized in LabRow.EXPECTED_RANGES
        return LabRow(
            raw_name=name,
            normalized_name=normalized,
            value=value,
            unit=unit,
            reference_range=ref_range,
            source=source,
            known_metric=known_metric,
        )

    return None


def parse_pdf_bytes(
    pdf_bytes: bytes,
    options: ParserOptions = ParserOptions(),
    ocr_fn: Optional[Callable[[bytes], str]] = None,
) -> PatientBundle:
    """Parse PDF bytes into a PatientBundle using text extraction and optional OCR."""

    text = extract_text_from_pdf(pdf_bytes)
    bundle: Optional[PatientBundle] = None

    if text:
        try:
            bundle = parse_text_rows(text, source=options.source, patient_id=options.patient_id)
        except ValidationError:
            bundle = None

    if (bundle is None or not bundle.rows) and ocr_fn:
        text = ocr_fn(pdf_bytes)
        bundle = parse_text_rows(text, source=options.source, patient_id=options.patient_id)

    if bundle is None:
        raise ValueError("Failed to parse PDF bytes")
    return bundle


def append_bundle_to_table(
    bundles: Iterable[PatientBundle], table: Optional[ContinuousResultsTable] = None
) -> ContinuousResultsTable:
    table = table or ContinuousResultsTable()
    for bundle in bundles:
        table.append(bundle)
    return table


__all__ = [
    "ParserOptions",
    "append_bundle_to_table",
    "extract_text_from_pdf",
    "parse_pdf_bytes",
    "parse_text_rows",
]
