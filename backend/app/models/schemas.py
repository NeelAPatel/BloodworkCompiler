from __future__ import annotations

from datetime import date
from typing import ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class ReferenceRange(BaseModel):
    """Represents the expected numeric bounds for a lab metric."""

    lower: Optional[float] = Field(default=None, description="Lower bound of normal range")
    upper: Optional[float] = Field(default=None, description="Upper bound of normal range")

    model_config = ConfigDict(extra="forbid")

    @field_validator("upper")
    @classmethod
    def validate_upper(cls, upper: Optional[float], info):
        lower = info.data.get("lower")
        if upper is not None and lower is not None and upper < lower:
            raise ValueError("upper must be >= lower")
        return upper


class LabRow(BaseModel):
    """Normalized representation of a single lab metric measurement."""

    raw_name: str = Field(description="Name as it appeared in the report")
    normalized_name: str = Field(description="Canonical metric name used in the app")
    value: float = Field(description="Numeric measurement value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    reference_range: Optional[ReferenceRange] = Field(
        default=None, description="Expected lower/upper bounds"
    )
    observed_at: Optional[date] = Field(
        default=None, description="Collection date of the sample when known"
    )
    source: str = Field(default="unknown", description="Originating lab or upload source")
    known_metric: bool = Field(
        default=True, description="Indicates if the metric is in the known range catalog"
    )

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    # expected unit and plausible range per metric (values are conservative bounds)
    EXPECTED_RANGES: ClassVar[Dict[str, ReferenceRange]] = {
        "hemoglobin": ReferenceRange(lower=5, upper=25),
        "ldl": ReferenceRange(lower=0, upper=300),
        "glucose": ReferenceRange(lower=40, upper=400),
        "vitamin d": ReferenceRange(lower=5, upper=120),
    }
    EXPECTED_UNITS: ClassVar[Dict[str, str]] = {
        "hemoglobin": "g/dL",
        "ldl": "mg/dL",
        "glucose": "mg/dL",
        "vitamin d": "ng/mL",
    }

    @field_validator("normalized_name")
    @classmethod
    def normalize_name(cls, normalized_name: str) -> str:
        normalized = normalized_name.strip().lower()
        if not normalized:
            raise ValueError("normalized_name must not be empty")
        return normalized

    @field_validator("value")
    @classmethod
    def enforce_range(cls, value: float, info):
        normalized = (info.data.get("normalized_name") or "").lower()
        expected_range = cls.EXPECTED_RANGES.get(normalized)
        if expected_range:
            lower = expected_range.lower
            upper = expected_range.upper
            if lower is not None and value < lower:
                raise ValueError(f"value for {normalized} below expected lower bound {lower}")
            if upper is not None and value > upper:
                raise ValueError(f"value for {normalized} above expected upper bound {upper}")
        return value

    @field_validator("unit")
    @classmethod
    def enforce_unit(cls, unit: Optional[str], info):
        normalized = (info.data.get("normalized_name") or "").lower()
        expected_unit = cls.EXPECTED_UNITS.get(normalized)
        if expected_unit and unit and unit != expected_unit:
            raise ValueError(f"Unit for {normalized} must be {expected_unit}")
        return unit

    @computed_field
    @property
    def has_reference_range(self) -> bool:
        return self.reference_range is not None


class PatientBundle(BaseModel):
    """Represents a batch of lab rows extracted from a single upload."""

    patient_id: Optional[str] = Field(default=None, description="Identifier when provided")
    rows: List[LabRow] = Field(default_factory=list)
    source: str = Field(default="unknown")

    model_config = ConfigDict(extra="forbid")

    @field_validator("rows")
    @classmethod
    def ensure_rows_not_empty(cls, rows: List[LabRow]) -> List[LabRow]:
        if not rows:
            raise ValueError("PatientBundle requires at least one LabRow")
        return rows


class ContinuousResultsTable(BaseModel):
    """Columnar table that appends a new column for each upload."""

    table: Dict[str, List[Optional[float]]] = Field(default_factory=dict)
    units: Dict[str, Optional[str]] = Field(default_factory=dict)
    reference_ranges: Dict[str, Optional[ReferenceRange]] = Field(default_factory=dict)
    uploads: int = 0

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    def append(self, bundle: PatientBundle) -> None:
        """Append a new upload column using rows from the bundle."""

        # extend all existing metric lists with None for this new upload
        for values in self.table.values():
            if len(values) < self.uploads + 1:
                values.append(None)

        for row in bundle.rows:
            metric = row.normalized_name
            if metric not in self.table:
                # backfill previous uploads with None
                self.table[metric] = [None for _ in range(self.uploads)]
                self.units[metric] = row.unit
                self.reference_ranges[metric] = row.reference_range
            metric_values = self.table[metric]
            if len(metric_values) < self.uploads + 1:
                metric_values.append(row.value)
            else:
                metric_values[self.uploads] = row.value

        self.uploads += 1

    def get_metric_values(self, metric: str) -> List[Optional[float]]:
        return self.table.get(metric, [])

