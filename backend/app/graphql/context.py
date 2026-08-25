import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext
from app.core.database import async_session_factory
from app.graphql.dataloaders import AppDataLoaders
from app.models.user import User


class GraphQLContext(BaseContext):
    def __init__(
        self,
        session: AsyncSession,
        loaders: AppDataLoaders | None = None,
        current_user: User | None = None,
    ):
        super().__init__()
        self.session = session
        self.lock = asyncio.Lock()
        self.loaders = loaders or AppDataLoaders(session, self.lock)
        self.current_user = current_user

    async def execute(self, stmt):
        async with self.lock:
            return await self.session.execute(stmt)

    async def commit(self):
        async with self.lock:
            return await self.session.commit()


async def get_graphql_context() -> AsyncGenerator[GraphQLContext, None]:
    async with async_session_factory() as session:
        ctx = GraphQLContext(session=session, current_user=None)
        try:
            yield ctx
        finally:
            await session.close()
