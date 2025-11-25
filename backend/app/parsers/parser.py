"""High-level orchestrator that extracts text, metadata, and lab results."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

from .metadata_extractor import extract_patient_metadata
from .pdf_loader import extract_text_with_fallback
from .result_extractor import extract_lab_results
from .types import ContinuousResultsTable, ParsedDocument


class LabPdfParser:
    """Parse one or many PDF reports into normalized structures."""

    def __init__(self, resolution: int = 300):
        self.resolution = resolution

    def parse(self, pdf_path: Path) -> ParsedDocument:
        raw_text = extract_text_with_fallback(pdf_path, resolution=self.resolution)
        metadata = extract_patient_metadata(raw_text)
        lines = [line for line in raw_text.splitlines() if line.strip()]
        results = extract_lab_results(lines, metadata.primary_collection_date)
        return ParsedDocument(source_path=Path(pdf_path), raw_text=raw_text, metadata=metadata, results=results)

    def parse_many(self, pdf_paths: Iterable[Path]) -> Tuple[List[ParsedDocument], ContinuousResultsTable]:
        """Iterate over multiple PDFs, aggregating the longitudinal results table."""

        documents: List[ParsedDocument] = []
        table = ContinuousResultsTable()

        for path in pdf_paths:
            document = self.parse(Path(path))
            documents.append(document)
            table.add_results(document.results)

        return documents, table
