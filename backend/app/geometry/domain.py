from dataclasses import dataclass
from enum import StrEnum

from shapely import Polygon, is_valid_reason


class PolygonErrorMessage(StrEnum):
    zero_area_after_setback = "Setback is too high, the resulting footprint has 0 area."
    divided_after_setback = "Setback is too high: the footprint is not in one piece"

PEM = PolygonErrorMessage
    
@dataclass
class SitePolygon:
    points: list[list[float]]

    @property
    def area(self) -> float:
        return Polygon(self.points).area

    def get_inset_check_valid(self, setback: float) -> tuple[Polygon | None, str]:
        polygon = Polygon(self.points)
        if not polygon.is_valid:
            return None, is_valid_reason(polygon)

        polygon = polygon.buffer(-setback)
        if polygon.geom_type == "MultiPolygon":
            return None, PEM.divided_after_setback.value
        
        if polygon.area == 0:
            return None, PEM.zero_area_after_setback.value
        
        return polygon, ""


MIN_SITE_COVERAGE_RATIO = 0.05
    
class ConstraintErrorMessage(StrEnum):
    site_coverage_ration_limits = f"Site coverage ratio should be at least {MIN_SITE_COVERAGE_RATIO} and at most 1"
    max_height_less_than_floor = "Max height is less then the height of one floor"

CEM = ConstraintErrorMessage

@dataclass
class Constraint:
    setback: float
    max_height: float
    max_floor_count: int
    floor_height: float
    site_coverage_ratio: float

    max_footprint_area: float | None
    gfa_target: float | None
    far_target: float | None

    def check_valid(self) -> ConstraintErrorMessage | None:
        if self.site_coverage_ratio < MIN_SITE_COVERAGE_RATIO or self.site_coverage_ratio > 1:
            return CEM.site_coverage_ration_limits
        if self.max_height < self.floor_height:
            return CEM.max_height_less_than_floor
        
        

@dataclass
class MassingResult:
    footprint_points: list[list[float]]
    footprint_area: float
    setback: float
    site_coverage_ratio: float
    gfa: float
    height: float
    floor_count: int
