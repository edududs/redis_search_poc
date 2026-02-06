"""Endpoints internos (ex.: shutdown para run-main --clean)."""

import os
import signal
from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from api.auth import get_api_key

router = APIRouter(prefix="/internal", tags=["internal"])


def _exit_process() -> None:
    """Encerra o processo. Com uvicorn --reload, mata o reloader (pai) para não reiniciar."""
    parent = os.getppid()
    if parent != 1:
        with suppress(OSError):
            os.kill(parent, signal.SIGTERM)
    os._exit(0)


@router.post("/shutdown")
def shutdown(
    _: Annotated[str, Depends(get_api_key)],
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Encerra o processo da API (uso: run-main --clean). Resposta 200 antes de derrubar."""
    background_tasks.add_task(_exit_process)
    return JSONResponse(content={"status": "shutting down"}, status_code=200)
