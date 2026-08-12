from fastapi import APIRouter, Request

from app.db import ensure_db, get_connection, purge_db

router = APIRouter(prefix="/db", tags=["db"])


@router.get("/ensure")
async def ensure_db_endpoint(request: Request) -> None:
    async for conn in get_connection(request.app.state.db_pool):
        await ensure_db(conn)
        await conn.commit()

@router.get("/purge")
async def purge_db_endpoint(request: Request) -> None:
    async for conn in get_connection(request.app.state.db_pool):
        await purge_db(conn)
        await conn.commit()
