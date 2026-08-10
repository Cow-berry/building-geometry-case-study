"""Database plumbing — async psycopg with a connection pool.

This wires up an async connection pool and a FastAPI dependency that hands you a
connection. There is **no ORM and no schema** on purpose: define your own model
types (plain dataclasses / pydantic) and write **pure SQL** with psycopg.

Example usage in a route:

    from psycopg import AsyncConnection
    from psycopg.rows import dict_row

    async def list_options(conn: AsyncConnection = Depends(get_connection)):
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT id, parent_id, name FROM options")
            return await cur.fetchall()

Wire the dependency to the app's pool however you prefer (e.g. a small provider
that reads `request.app.state.db_pool`).
"""

from collections.abc import AsyncGenerator
from dataclasses import asdict, dataclass
from typing import ClassVar, LiteralString, cast, override

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.config import Config


def create_pool(config: Config) -> AsyncConnectionPool:
    # open=False: the pool is opened in the app lifespan, not at import time.
    return AsyncConnectionPool(config.database_url, open=False)


async def get_connection(pool: AsyncConnectionPool) -> AsyncGenerator[AsyncConnection, None]:
    async with pool.connection() as conn:
        yield conn


@dataclass
class DBTable:
    id: int

    ignore_check: ClassVar[list[str]] = ["id"]

    @classmethod
    def table_name(cls) -> str:
        return "".join([c if c.islower() else f"_{c.lower()}" for c in cls.__name__]).lstrip("_") + "s"

    @classmethod
    def create_table(cls) -> str:
        return ""

    @classmethod
    def drop_table(cls) -> LiteralString:
        return cast(LiteralString, f"DROP TABLE IF EXISTS {cls.table_name()} CASCADE;")

    def _get_data(self) -> dict:
        data = asdict(self)
        for ignore in self.ignore_check:
            if ignore in data:
                data.pop(ignore)
        return data

    async def insert(self, conn: AsyncConnection) -> int:
        data = self._get_data()
        query: LiteralString = cast(
            LiteralString,
            f"""\
        INSERT INTO {self.table_name()}({",".join(data)}) VALUES ({",".join(["%s"] * len(data))}) RETURNING id;\
        """,
        )
        async with conn.cursor() as cur:
            await cur.execute(query, [data[key] for key in data])
            id = await cur.fetchone()
            assert id is not None

            return id[0]

    async def check_or_insert(self, conn: AsyncConnection) -> int:
        data = self._get_data()
        query = cast(
            LiteralString,
            f"""\
        SELECT * FROM {self.table_name()}\
        WHERE {" AND ".join([name + " " + ("= %s" if data[name] is not None else "is null") + "" for name in data])};
        """,
        )

        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, [data[key] for key in data if data[key] is not None])
            row = await cur.fetchone()
            print(f"\n{self.__class__.__name__} {row = }\n{query = }\n{data = }")
            if row is not None:
                return row["id"]
            print(f"{row = } IS NONE")
            return await self.insert(conn)


@dataclass
class SitePolygon(DBTable):
    points: list[list[float]]

    @override
    @classmethod
    def create_table(cls) -> str:
        return f"""\
        CREATE TABLE IF NOT EXISTS {cls.table_name()} (
            id serial primary key,
            points double precision[] not null
        );
        """


@dataclass
class Constraint(DBTable):
    setback: float
    max_height: float
    max_floor_count: int
    floor_height: float
    site_coverage_ratio: float

    max_footprint_area: float | None
    gfa_target: float | None
    far_target: float | None

    @override
    @classmethod
    def create_table(cls) -> str:
        return f"""\
        CREATE TABLE IF NOT EXISTS {cls.table_name()} (
            id serial primary key,
            setback double precision not null,
            max_height double precision not null,
            max_floor_count int not null,
            floor_height double precision not null,
            site_coverage_ratio double precision not null,
            max_footprint_area double precision,
            gfa_target double precision,
            far_target double precision
        );
        """


@dataclass
class MassingResult(DBTable):
    footprint_points: list[list[float]]
    footprint_area: float
    setback: float
    site_coverage_ratio: float
    gfa: float
    height: float
    floor_count: int

    @override
    @classmethod
    def create_table(cls) -> str:
        return f"""\
        CREATE TABLE IF NOT EXISTS {cls.table_name()} (
            id serial primary key,
            footprint_points double precision[] not null,
            footprint_area double precision not null,
            setback double precision not null,
            site_coverage_ratio double precision not null,
            gfa double precision not null,
            height double precision not null,
            floor_count int not null
        );
        """


@dataclass
class Massing(DBTable):
    polygon_id: int
    constraint_id: int
    result_id: int
    parent_id: int | None

    ignore_check: ClassVar[list[str]] = ["id", "parent_id"]

    @override
    @classmethod
    def create_table(cls) -> str:
        return f"""\
        CREATE TABLE IF NOT EXISTS {cls.table_name()} (
            id serial primary key,
            polygon_id int not null,
            constraint_id int not null,
            result_id int not null,
            parent_id int
        );
        """

    @classmethod
    async def get_all(cls, conn: AsyncConnection) -> list[dict]:
        async with conn.cursor(row_factory=dict_row) as cur:
            query: LiteralString = cast(
                LiteralString,
                f"""
SELECT {Massing.table_name()}, {SitePolygon.table_name()}, {Constraint.table_name()}, {MassingResult.table_name()}
FROM {Massing.table_name()}
LEFT JOIN {SitePolygon.table_name()} ON {Massing.table_name()}.polygon_id = {SitePolygon.table_name()}.id
LEFT JOIN {Constraint.table_name()} ON {Massing.table_name()}.constraint_id = {Constraint.table_name()}.id
LEFT JOIN {MassingResult.table_name()} ON {Massing.table_name()}.result_id = {MassingResult.table_name()}.id
            """,
            )
            await cur.execute(query)
            return await cur.fetchall()


async def purge_db(conn: AsyncConnection):
    scripts = [cls.drop_table() for cls in DBTable.__subclasses__()]
    query: LiteralString = cast(LiteralString, "\n".join(scripts))

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(query)


async def ensure_db(conn: AsyncConnection):
    # await purge_db(conn)
    # await conn.commit()
    scripts = [cls.create_table() for cls in DBTable.__subclasses__()]
    query: LiteralString = cast(LiteralString, "\n".join(scripts))

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(query)
