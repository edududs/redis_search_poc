"""Endpoints para obter e criar usuários."""

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import get_api_key
from api.deps import get_user_repository
from api.schemas import UserCreate, UserResponse

if TYPE_CHECKING:
    from api.crud import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
def get_user(
    user_id: str,
    _: Annotated[str, Depends(get_api_key)],
    repo: Annotated["UserRepository", Depends(get_user_repository)],
) -> UserResponse:
    """Retorna usuário pelo id ou 404."""
    user = repo.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado"
        )
    return user


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    _: Annotated[str, Depends(get_api_key)],
    repo: Annotated["UserRepository", Depends(get_user_repository)],
) -> UserResponse:
    """Cria usuário novo, ou 409 se já existe."""
    existing = repo.get(body.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Usuário {body.id} já existe",
        )
    return repo.insert(body)
