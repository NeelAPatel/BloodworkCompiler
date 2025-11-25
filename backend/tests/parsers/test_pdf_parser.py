from pathlib import Path

import pytest

from app.models import ContinuousResultsTable, LabRow, ReferenceRange
from app.parsers import ParserOptions, append_bundle_to_table, parse_pdf_bytes

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "pdfs"


def test_parse_text_pdf_fixture():
    pdf_bytes = (FIXTURE_DIR / "text_report.pdf").read_bytes()

    bundle = parse_pdf_bytes(pdf_bytes, options=ParserOptions(source="LabCorp", patient_id="abc"))

    assert bundle.source == "LabCorp"
    assert len(bundle.rows) == 3

    hemoglobin = bundle.rows[0]
    assert hemoglobin.normalized_name == "hemoglobin"
    assert hemoglobin.unit == "g/dL"
    assert hemoglobin.reference_range == ReferenceRange(lower=12.0, upper=16.0)

    glucose = bundle.rows[2]
    assert glucose.reference_range.lower == 70
    assert glucose.reference_range.upper == 99
    assert glucose.known_metric is True


def test_sequential_uploads_append_columns():
    first = parse_pdf_bytes((FIXTURE_DIR / "text_report.pdf").read_bytes())
    follow_up = parse_pdf_bytes((FIXTURE_DIR / "followup_report.pdf").read_bytes())

    table = append_bundle_to_table([first])
    assert table.uploads == 1
    assert table.get_metric_values("hemoglobin") == [13.2]

    table = append_bundle_to_table([follow_up], table=table)

    assert table.uploads == 2
    assert table.get_metric_values("hemoglobin") == [13.2, 13.4]
    # LDL and Glucose are missing on follow-up and should backfill None
    assert table.get_metric_values("ldl") == [98.0, None]
    assert table.get_metric_values("glucose") == [92.0, None]
    # Vitamin D arrives only on the second upload
    assert table.get_metric_values("vitamin d") == [None, 35.1]


def test_ocr_fallback_for_image_fixture():
    pdf_bytes = (FIXTURE_DIR / "image_report.pdf").read_bytes()
    calls = []

    def fake_ocr(data: bytes) -> str:
        calls.append(len(data))
        return "Hemoglobin,12.9,g/dL,12-16\nLDL,101,mg/dL,0-130"

    bundle = parse_pdf_bytes(pdf_bytes, options=ParserOptions(source="Quest"), ocr_fn=fake_ocr)

    assert calls, "OCR fallback should have been used"
    assert len(bundle.rows) == 2
    assert all(row.source == "Quest" for row in bundle.rows)


def test_unknown_metric_is_preserved():
    pdf_bytes = (FIXTURE_DIR / "followup_report.pdf").read_bytes()

    bundle = parse_pdf_bytes(pdf_bytes, options=ParserOptions(source="Lab"))

    omega = next(row for row in bundle.rows if row.normalized_name == "omega3 index")
    assert isinstance(omega, LabRow)
    assert omega.known_metric is False
    assert omega.reference_range is None


if __name__ == "__main__":
    pytest.main([__file__])
