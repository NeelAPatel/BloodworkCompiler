"""Parse lab result rows from PDF text content."""
from __future__ import annotations

import re
from datetime import date
from typing import Iterable, List

from .types import LabResultRow


ROW_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z0-9 /()\-]+)\s+"
    r"(?P<value>[<>]?[0-9.]+|POS|NEG|NR)\s+"
    r"(?P<units>[A-Za-z/%µ]+)?\s*"
    r"(?P<flag>H|L|HIGH|LOW|\*)?\s*"
    r"(?P<range>[0-9.\-–]+\s*[A-Za-z/%µ]*)",
    re.IGNORECASE,
)


def extract_lab_results(lines: Iterable[str], collection_date: date | None) -> List[LabResultRow]:
    """Return lab result rows captured from a block of text lines."""

    results: List[LabResultRow] = []
    for raw_line in lines:
        line = raw_line.strip()
        match = ROW_PATTERN.match(line)
        if match:
            results.append(
                LabResultRow(
                    test_name=match.group("name").strip(),
                    value=match.group("value"),
                    units=match.group("units"),
                    flag=match.group("flag"),
                    reference_range=match.group("range"),
                    collection_date=collection_date,
                )
            )
            continue

        # Lines that do not match the regex can be escalated to an AI model.
        # This preserves the hook for hybrid parsing of harder OCR outputs.
    return results
