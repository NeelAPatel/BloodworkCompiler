"""Helpers to identify patient metadata from extracted PDF text."""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from .types import PatientMetadata


DOB_PATTERNS = [
    re.compile(r"DOB[:\s]+(?P<dob>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", re.IGNORECASE),
    re.compile(r"Date of Birth[:\s]+(?P<dob>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", re.IGNORECASE),
]
COLLECTION_PATTERNS = [
    re.compile(r"Collection Date[:\s]+(?P<col>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", re.IGNORECASE),
    re.compile(r"Collected[:\s]+(?P<col>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", re.IGNORECASE),
]
ADDRESS_PATTERN = re.compile(r"\d+\s+\w+[\w\s,.]+\d{5}")


def extract_patient_metadata(text: str) -> PatientMetadata:
    """Pull out patient metadata using simple heuristics and regexes."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    metadata = PatientMetadata()

    metadata.name = _guess_name(lines)
    metadata.addresses = _find_addresses(lines)
    metadata.date_of_birth = _match_first_date(lines, DOB_PATTERNS)
    metadata.collection_dates = _find_all_dates(lines, COLLECTION_PATTERNS)
    metadata.lab_company = _guess_lab_company(lines)

    return metadata


def _guess_name(lines: List[str]) -> Optional[str]:
    for line in lines[:5]:
        if any(token in line.lower() for token in ["patient", "name"]):
            return line.split(":")[-1].strip()
    return lines[0] if lines else None


def _find_addresses(lines: List[str]) -> List[str]:
    addresses: List[str] = []
    for line in lines:
        if ADDRESS_PATTERN.search(line):
            addresses.append(line)
    return addresses


def _match_first_date(lines: List[str], patterns: List[re.Pattern[str]]) -> Optional[datetime.date]:
    for line in lines:
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                raw = match.group("dob") if "dob" in match.groupdict() else match.group("col")
                parsed = _parse_date(raw)
                if parsed:
                    return parsed
    return None


def _find_all_dates(lines: List[str], patterns: List[re.Pattern[str]]) -> List[datetime.date]:
    dates: List[datetime.date] = []
    for line in lines:
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                raw = match.group("col") if "col" in match.groupdict() else match.group(1)
                parsed = _parse_date(raw)
                if parsed:
                    dates.append(parsed)
    return dates


def _parse_date(raw: str) -> Optional[datetime.date]:
    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _guess_lab_company(lines: List[str]) -> Optional[str]:
    if not lines:
        return None
    header = lines[0].strip()
    if "labcorp" in header.lower():
        return "Labcorp"
    if "quest" in header.lower():
        return "Quest Diagnostics"
    if "laboratory" in header.lower() or "lab" in header.lower():
        return header
    return None
