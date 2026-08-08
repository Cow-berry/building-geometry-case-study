from app.geometry.domain import Constraint, SitePolygon, MassingResult, PEM, CEM
from app.geometry.algorithm import calculate_massing

import pytest


modest_constraints = Constraint(3, 24, 6, 3.5, 0.6, None, None, None)
tower_constraints = Constraint(3, 80, 20, 4, 1, None, 9000, None)
infeasible_constraints = Constraint(12, 10, 3, 3.5, 0.5, None, None, None)


square_points: list[list[float]] = [[0,0],[0,10],[10,10],[10,0]]
l_shaped: list[list[float]] = [[0, 0], [40, 0], [40, 15], [20, 15], [20, 30], [0, 30]]
notched: list[list[float]] =  [[0, 0], [50, 0], [50, 20], [30, 20], [30, 6], [20, 6], [20, 20], [0, 20]]
rectangle: list[list[float]] = [[0, 0], [40, 0], [40, 25], [0, 25]]



def test_simple():
    points: list[list[float]] = square_points
    polygon = SitePolygon(points)
    constraints = Constraint(3, 10, 5, 2, 0.25, None, None, None)
    res, _ = calculate_massing(polygon, constraints)

    expected_footprint = [[3.0, 3.0], [3.0, 7.0], [7.0, 7.0], [7.0, 3.0]]
    expected = MassingResult(expected_footprint, 16, 3, 0.16, 80, 10, 5) # all numbers are different to test positions
    assert res == expected

def test_optimize():
    points: list[list[float]] = square_points
    polygon = SitePolygon(points)
    constraints = Constraint(0, 20, 20, 1, 0.314, None, None, None)
    res, _ = calculate_massing(polygon, constraints)
    assert res is not None
    assert res.site_coverage_ratio < 0.314


@pytest.mark.parametrize("constraints", [
    modest_constraints,
    tower_constraints,
    infeasible_constraints
])
def test_l_shaped(constraints):
    points: list[list[float]] = l_shaped
    polygon = SitePolygon(points)
    res, _ = calculate_massing(polygon, constraints)

    if constraints == infeasible_constraints:
        assert res is None
        return

    assert res is not None

@pytest.mark.parametrize("constraints", [
    modest_constraints,
    tower_constraints,
    infeasible_constraints
])
def test_notched(constraints):
    points: list[list[float]] = notched
    polygon = SitePolygon(points)
    res, err = calculate_massing(polygon, constraints)

    assert res is None
    if constraints == infeasible_constraints:
        assert err == PEM.zero_area_after_setback.value
        return
    assert err == PEM.divided_after_setback.value

def test_invalid():
    points: list[list[float]] = [[0,0], [1,1], [1, 0], [0,1]]
    polygon = SitePolygon(points)
    res, err = calculate_massing(polygon, modest_constraints)
    assert res is None

def test_max_height_less_than_floor_height():
    points: list[list[float]] = l_shaped
    constraints = Constraint(0, 2, 20, 3, 1, None, None, None)
    polygon = SitePolygon(points)
    res, err = calculate_massing(polygon, constraints)
    assert res is None
    assert err == CEM.max_height_less_than_floor.value

def test_site_coverage_ration_limits():
    points: list[list[float]] = l_shaped
    constraints = Constraint(0, 3, 20, 2, 1e-3, None, None, None)
    polygon = SitePolygon(points)
    res, err = calculate_massing(polygon, constraints)
    assert res is None
    assert err == CEM.site_coverage_ration_limits

    constraints = Constraint(0, 3, 20, 2, 1.1, None, None, None)
    polygon = SitePolygon(points)
    res, err = calculate_massing(polygon, constraints)
    assert res is None
    assert err == CEM.site_coverage_ration_limits
