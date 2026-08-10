from fastapi import APIRouter, Request

from app.db import ensure_db, get_connection

router = APIRouter(prefix="/db", tags=["db"])


@router.get("/ensure")
async def ensure_bd(request: Request) -> None:
    async for conn in get_connection(request.app.state.db_pool):
        await ensure_db(conn)
        await conn.commit()
