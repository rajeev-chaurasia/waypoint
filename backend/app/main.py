from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from app.core.config import settings
from app.core.database import Base, async_session_factory, engine
from app.graphql.context import get_graphql_context
from app.graphql.schema import schema
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed initial test data
    async with async_session_factory() as session:
        await seed_database(session)

    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
)

app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "waypoint",
        "version": "1.0.0",
        "graphql_endpoint": "/graphql",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
