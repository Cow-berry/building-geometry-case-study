from enum import StrEnum

from shapely import Polygon

from .domain import Constraint, MassingResult, SitePolygon


class AlgorithmErrorMessage(StrEnum):
    infeasible = "Infeasible constraints. Try easier targets."


AEM = AlgorithmErrorMessage


def optimize_setback(site_polygon: SitePolygon, constraint: Constraint) -> tuple[Polygon, float]:
    site_polygon_diameter = constraint.setback
    for x1, y1 in site_polygon.points:
        for x2, y2 in site_polygon.points:
            distance12 = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            site_polygon_diameter = max(site_polygon_diameter, distance12)

    a = constraint.setback
    b = site_polygon_diameter
    site_polygon_area = site_polygon.area
    footprint = None

    # find working high limit
    # a is guaranteed to work
    # b is guaranteed to fail
    while (b - a) > 1e-12:
        setback = b - (b - a) / 2
        footprint, _ = site_polygon.get_inset_check_valid(setback)
        if footprint is None:
            b = setback
        else:
            a = setback

    b = a
    a = constraint.setback

    while (b - a) > 1e-12:
        setback = b - (b - a) / 2
        footprint, _ = site_polygon.get_inset_check_valid(setback)
        assert footprint is not None  # can be done because both limits work

        site_coverage_ratio = footprint.area / site_polygon_area
        if site_coverage_ratio > constraint.site_coverage_ratio:
            a = setback
        elif constraint.max_footprint_area is not None and footprint.area > constraint.max_footprint_area:
            a = setback
        else:
            b = setback

    # specifically `b` because setback at `a` does not satisfy the constraint (i.e. we prefer cutting more then less)
    result_setback = b
    rounded = round(result_setback, 3)
    if rounded >= a:
        result_setback = rounded
    footprint, _ = site_polygon.get_inset_check_valid(result_setback)
    assert footprint is not None

    return footprint, result_setback


def calculate_massing(site_polygon: SitePolygon, constraint: Constraint) -> tuple[MassingResult | None, str]:
    err = constraint.check_valid()
    if err is not None:
        return None, err.value

    footprint, err = site_polygon.get_inset_check_valid(constraint.setback)
    if footprint is None:
        return None, err

    footprint, setback = optimize_setback(site_polygon, constraint)
    footprint_points: list[list[float]] = [list(x) for x in list(footprint.boundary.coords)[:-1]]
    footprint_area: float = footprint.area
    site_coverage_ratio = footprint_area / site_polygon.area

    possible_max_floor_count: int = int(constraint.max_height / constraint.floor_height)
    true_max_floor_count: int = min(possible_max_floor_count, constraint.max_floor_count)
    floor_count_options: list[MassingResult] = []
    for floor_count in range(1, true_max_floor_count + 1):
        gfa = footprint.area * floor_count
        height = constraint.floor_height * floor_count
        floor_count_options.append(
            MassingResult(footprint_points, footprint_area, setback, site_coverage_ratio, gfa, height, floor_count)
        )

    gfa_target = constraint.gfa_target
    if gfa_target is None and constraint.far_target is not None:
        gfa_target = constraint.far_target * site_polygon.area

    if len(floor_count_options) == 0:
        return None, AEM.infeasible.value

    if gfa_target is None:
        return max(floor_count_options, key=lambda option: option.floor_count), ""

    floor_count_options = [option for option in floor_count_options if option.gfa >= gfa_target]

    if len(floor_count_options) == 0:
        return None, AEM.infeasible.value

    return min(floor_count_options, key=lambda option: option.gfa), ""
