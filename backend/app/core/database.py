import contextvars
from collections.abc import AsyncGenerator
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

_active_query_counter = None


class Base(DeclarativeBase):
    pass


class QueryCounter:
    """Context manager to measure exact number of SQL queries executed."""

    def __init__(self, collect_statements: bool = False):
        self.collect_statements = collect_statements
        self.count = 0
        self.statements: list[str] = []

    def __enter__(self):
        global _active_query_counter
        self.count = 0
        self.statements = []
        _active_query_counter = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _active_query_counter
        _active_query_counter = None


def create_engine_and_session(
    database_url: str = settings.DATABASE_URL,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    connect_args = {}
    if "sqlite" in database_url:
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
        connect_args=connect_args,
    )

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def receive_before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        global _active_query_counter
        if _active_query_counter is not None:
            _active_query_counter.count += 1
            if _active_query_counter.collect_statements:
                _active_query_counter.statements.append(statement)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, session_factory


engine, async_session_factory = create_engine_and_session()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


