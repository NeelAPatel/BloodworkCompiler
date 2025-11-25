"""
CLI entrypoint for running the proof-of-concept bloodwork parser locally.

Usage examples (from the repository root):

    python -m backend.app.parsers.run_local data/sample_pdfs/report.pdf
    python -m backend.app.parsers.run_local data/sample_pdfs/a.pdf data/sample_pdfs/b.pdf \
        --csv-out data/fixtures/parsed_results.csv \
        --parquet-out data/fixtures/parsed_results.parquet \
        --table-out data/fixtures/results_table.csv

The command accepts one or more PDF paths, runs a lightweight parser stub, and
writes structured results to both CSV and Parquet outputs alongside a snapshot
of the continuous results table.
"""
from __future__ import annotations

import argparse
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, MutableMapping

LOGGER = logging.getLogger(__name__)


ParsedRow = MutableMapping[str, str]


def _default_output_paths() -> tuple[Path, Path, Path]:
    base_dir = Path(__file__).resolve().parents[3] / "data" / "fixtures"
    return (
        base_dir / "parsed_results.csv",
        base_dir / "parsed_results.parquet",
        base_dir / "results_table.csv",
    )


def parse_pdf(path: Path) -> List[ParsedRow]:
    """Return a lightweight structured representation of a PDF.

    The current implementation focuses on deterministic, file-level metadata so
    the CLI works without heavy PDF dependencies. When a richer parser exists,
    this function can be swapped to return true analyte-level rows.
    """

    text_excerpt: str
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(path) as pdf:  # pragma: no cover - optional dependency
            first_page = pdf.pages[0] if pdf.pages else None
            text_excerpt = (first_page.extract_text() or "").strip()[:256] if first_page else ""
    except Exception:  # pragma: no cover - optional dependency or parsing failure
        # Fall back to a simple file signature to avoid hard failures when
        # pdfplumber is unavailable.
        LOGGER.debug("Falling back to stub parsing for %s", path)
        text_excerpt = ""

    return [
        {
            "source_file": path.name,
            "analyte": "placeholder",
            "value": "",
            "unit": "",
            "reference_range": "",
            "collected_at": datetime.utcnow().isoformat(),
            "notes": "Parsed locally for smoke testing",
            "text_excerpt": text_excerpt,
        }
    ]


def _write_csv(rows: Iterable[ParsedRow], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        LOGGER.warning("No rows to write to %s", destination)
        return

    fieldnames = list(rows[0].keys())
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_parquet(rows: Iterable[ParsedRow], destination: Path) -> None:
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        LOGGER.warning("Skipping Parquet export (%s)", exc)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(list(rows))
    frame.to_parquet(destination, index=False)


def _build_continuous_results(rows: List[ParsedRow]) -> List[ParsedRow]:
    snapshot: List[ParsedRow] = []
    for index, row in enumerate(rows, start=1):
        enriched = dict(row)
        enriched["record_id"] = str(index)
        snapshot.append(enriched)
    return snapshot


def main(argv: list[str] | None = None) -> int:
    csv_out, parquet_out, table_out = _default_output_paths()

    parser = argparse.ArgumentParser(
        description="Parse one or more lab report PDFs and write structured outputs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "pdfs",
        nargs="+",
        type=Path,
        help="Path(s) to local PDF reports to parse.",
    )
    parser.add_argument("--csv-out", type=Path, default=csv_out, help="Structured CSV output path.")
    parser.add_argument(
        "--parquet-out",
        type=Path,
        default=parquet_out,
        help="Structured Parquet output path (requires pandas + pyarrow).",
    )
    parser.add_argument(
        "--table-out",
        type=Path,
        default=table_out,
        help="Continuous results table snapshot (CSV).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging for troubleshooting.",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    parsed_rows: List[ParsedRow] = []
    for pdf_path in args.pdfs:
        if not pdf_path.exists():
            LOGGER.error("PDF not found: %s", pdf_path)
            continue
        if pdf_path.suffix.lower() != ".pdf":
            LOGGER.error("Skipping non-PDF input: %s", pdf_path)
            continue

        try:
            parsed = parse_pdf(pdf_path)
            LOGGER.info("Parsed %d row(s) from %s", len(parsed), pdf_path)
            parsed_rows.extend(parsed)
        except Exception as exc:  # pragma: no cover - runtime safety
            LOGGER.exception("Failed to parse %s: %s", pdf_path, exc)

    if not parsed_rows:
        LOGGER.error("No parsed rows generated; nothing to write.")
        return 1

    _write_csv(parsed_rows, args.csv_out)
    LOGGER.info("Structured CSV written to %s", args.csv_out)

    _write_parquet(parsed_rows, args.parquet_out)
    LOGGER.info("Structured Parquet attempted at %s", args.parquet_out)

    snapshot = _build_continuous_results(parsed_rows)
    _write_csv(snapshot, args.table_out)
    LOGGER.info("Continuous results snapshot written to %s", args.table_out)

    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution
    raise SystemExit(main())
