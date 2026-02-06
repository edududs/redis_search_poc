"""Autenticação por chave de API (wrapper tipado)."""

import os
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

HTTP_BEARER = HTTPBearer(auto_error=False)


class ApiKeyValidator:
    """Valida o header Authorization: Bearer contra a chave configurada."""

    def __init__(self, expected_key: str | None = None) -> None:
        self._expected = (
            expected_key if expected_key is not None else os.getenv("API_KEY")
        )

    def validate(self, credentials: HTTPAuthorizationCredentials | None) -> str:
        """Retorna o token se válido; levanta HTTPException caso contrário."""
        if not self._expected:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API_KEY não configurada",
            )
        if not credentials or credentials.credentials != self._expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Chave de API inválida ou ausente",
            )
        return credentials.credentials


def get_api_key_validator() -> ApiKeyValidator:
    """Dependency: instância do validador (lê API_KEY do env)."""
    return ApiKeyValidator()


def get_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(HTTP_BEARER)],
    validator: Annotated[ApiKeyValidator, Depends(get_api_key_validator)],
) -> str:
    """Dependency: valida e retorna a chave de API."""
    return validator.validate(credentials)
