"""API de Fallback: API HTTP com SQLite para cenário de fallback em get-com-TTL do Redis."""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from api.deps import AppContainer
from api.routes import products, users

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = AppContainer()
    container.ensure_db()
    app.state.container = container
    yield


app = FastAPI(
    title="API de Fallback",
    description="API SQLite utilizada como fonte de verdade quando ocorrem cache misses no Redis (get com TTL).",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(products.router)


def run() -> None:
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="localhost",
        port=8000,
        reload=True,
    )
