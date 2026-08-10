from dataclasses import asdict

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.db import Constraint as DBConstraint
from app.db import Massing, get_connection
from app.db import Massing as DBMassing
from app.db import MassingResult as DBMassingResult
from app.db import SitePolygon as DBSitePolygon
from app.geometry.algorithm import calculate_massing
from app.geometry.domain import Constraint, MassingResult, SitePolygon

router = APIRouter(prefix="/massing", tags=["massing"])


@router.get("/get/all")
async def get_all(request: Request) -> list[dict]:
    async for conn in get_connection(request.app.state.db_pool):
        return await Massing.get_all(conn)
    return []


class CreateMassing(BaseModel):
    points: list[list[float]]
    constraint: dict
    parent: int | None


@router.post("/create")
async def create_massing(body: CreateMassing, request: Request) -> tuple[MassingResult | None, str | int]:
    try:
        polygon = SitePolygon(body.points)
        constraint = Constraint(**body.constraint)
        massing, err = calculate_massing(polygon, constraint)
        if massing is None:
            return None, err

        async for conn in get_connection(request.app.state.db_pool):
            db_polygon = await DBSitePolygon(-1, body.points).check_or_insert(conn)
            db_constraint = await DBConstraint(-1, **body.constraint).check_or_insert(conn)
            db_massing_result = await DBMassingResult(-1, **asdict(massing)).check_or_insert(conn)
            db_massing = await DBMassing(-1, db_polygon, db_constraint, db_massing_result, body.parent).insert(conn)
            await conn.commit()

            return massing, db_massing
        return None, "Internal Error: No database connection"

    except Exception as e:
        return None, f"Internal Error: {e}"
