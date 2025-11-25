"""Data models used by the PDF parsing pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PatientMetadata:
    """Lightweight container for patient information lifted from a PDF."""

    name: Optional[str] = None
    addresses: List[str] = field(default_factory=list)
    date_of_birth: Optional[date] = None
    collection_dates: List[date] = field(default_factory=list)
    lab_company: Optional[str] = None

    @property
    def primary_collection_date(self) -> Optional[date]:
        return self.collection_dates[0] if self.collection_dates else None


@dataclass
class LabResultRow:
    """Normalized representation of a single lab test result."""

    test_name: str
    value: Optional[str]
    units: Optional[str]
    flag: Optional[str]
    reference_range: Optional[str]
    collection_date: Optional[date]


@dataclass
class ParsedDocument:
    """Represents a fully parsed lab PDF with metadata and results."""

    source_path: Path
    raw_text: str
    metadata: PatientMetadata
    results: List[LabResultRow] = field(default_factory=list)


@dataclass
class ResultCell:
    """A single cell in the longitudinal results table."""

    value: Optional[str]
    flag: Optional[str]


@dataclass
class ContinuousResultsTable:
    """Longitudinal table that appends a column for every parsed PDF date."""

    values: Dict[str, Dict[str, ResultCell]] = field(default_factory=dict)
    units: Dict[str, Optional[str]] = field(default_factory=dict)
    reference_ranges: Dict[str, Optional[str]] = field(default_factory=dict)

    def add_result(self, result: LabResultRow) -> None:
        date_key = result.collection_date.isoformat() if result.collection_date else "unknown_date"
        test_row = self.values.setdefault(result.test_name, {})
        if date_key not in test_row:
            test_row[date_key] = ResultCell(value=result.value, flag=result.flag)
        self.units.setdefault(result.test_name, result.units)
        self.reference_ranges.setdefault(result.test_name, result.reference_range)

    def add_results(self, results: List[LabResultRow]) -> None:
        for result in results:
            self.add_result(result)

    def to_rows(self) -> List[Dict[str, Optional[str]]]:
        """Flatten the table into a list of dictionaries usable for CSV/JSON."""

        rows: List[Dict[str, Optional[str]]] = []
        all_dates: List[str] = sorted({date for cell in self.values.values() for date in cell.keys()})

        for test_name, date_cells in self.values.items():
            row: Dict[str, Optional[str]] = {
                "test_name": test_name,
                "units": self.units.get(test_name),
                "reference_range": self.reference_ranges.get(test_name),
            }
            for date_key in all_dates:
                cell = date_cells.get(date_key)
                row[date_key] = cell.value if cell else None
                row[f"{date_key}_flag"] = cell.flag if cell else None
            rows.append(row)

        return rows
