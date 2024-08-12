from enum import Enum
from dataclasses import dataclass
from typing import Any

class PermitType(str, Enum):
    commercial_wrecking_permit = "Building/Wrecking/Commercial/NA"
    residential_wrecking_permit = "Building/Wrecking/Residential/NA"


@dataclass
class BuildingServicesSearchResult:
    # TODO validation (regex?)
    record_number: str  # e.g. WRK2024R-00138
    record_details_link: str  # URL to the record details page
    record_type: PermitType
    project_name: str | None
    address: str
    expiration_date: Any | None  # I haven't found any records w/ this yet
    short_notes: str | None

    def __str__(self):
        return f"{self.record_type.value}:\n{self.record_number} - {self.project_name} - {self.address}"

