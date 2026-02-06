"""Container de dependências: Database e repositórios para injeção nas rotas (sem globais)."""

from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request

from api.crud import ProductRepository, UserRepository
from api.db import Database


class AppContainer:
    """Container com Database e repositórios; criado no lifespan e armazenado em app.state."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self._db_path = Path(db_path) if db_path is not None else None
        self._database: Database | None = None
        self._user_repo: UserRepository | None = None
        self._product_repo: ProductRepository | None = None

    def get_database(self) -> Database:
        """Retorna a instância única de Database (lazy)."""
        if self._database is None:
            self._database = Database(db_path=self._db_path)
        return self._database

    def get_user_repository(self) -> UserRepository:
        """Retorna o repositório de usuários (lazy)."""
        if self._user_repo is None:
            self._user_repo = UserRepository(self.get_database())
        return self._user_repo

    def get_product_repository(self) -> ProductRepository:
        """Retorna o repositório de produtos (lazy)."""
        if self._product_repo is None:
            self._product_repo = ProductRepository(self.get_database())
        return self._product_repo

    def ensure_db(self) -> None:
        """Garante que o schema do banco está criado (chamado no startup da app)."""
        self.get_database().init_schema()


def get_container(request: Request) -> AppContainer:
    """Dependency: retorna o container armazenado em app.state."""
    return request.app.state.container


def get_user_repository(
    container: Annotated[AppContainer, Depends(get_container)],
) -> UserRepository:
    """Dependency: repositório de usuários."""
    return container.get_user_repository()


def get_product_repository(
    container: Annotated[AppContainer, Depends(get_container)],
) -> ProductRepository:
    """Dependency: repositório de produtos."""
    return container.get_product_repository()
