import os
from typing import Self

import httpx
from redis import Redis
from redis.exceptions import RedisError


def get_redis_client(
    url: str | None = None,
    host: str = "localhost",
    port: int = 666,
    db: int = 0,
    *,
    decode_responses: bool = True,
) -> Redis:
    """Obtém um cliente Redis a partir de uma URL ou host/porta/banco.

    Args:
        url: URL de conexão do Redis. Se fornecida, tem precedência sobre host/port/db.
        host: Host do servidor Redis.
        port: Porta do servidor Redis.
        db: Número do banco de dados Redis.
        decode_responses: Se deve decodificar as respostas do Redis para strings.

    Returns:
        Redis: Instância do cliente Redis.

    Raises:
        RedisError: Se não for possível conectar ao Redis.

    """
    if url:
        client = Redis.from_url(url, decode_responses=decode_responses)
    else:
        client = Redis(host=host, port=port, db=db, decode_responses=decode_responses)
    if not client.ping():
        msg = "Falha ao conectar ao Redis"
        raise RedisError(msg)
    return client


DEFAULT_HTTP_TIMEOUT = 30.0


class ApiClient:
    """Cliente para chamadas à API."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_HTTP_TIMEOUT,
    ) -> None:
        """Inicializa o cliente da API."""
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> httpx.Response:
        headers = headers or {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            return client.request(method, path, params=params, json=data, headers=headers)

    def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> httpx.Response:
        """Envia uma requisição GET para a API.

        Args:
            url (str): URL do endpoint (relativa ao base_url).
            params (dict | None, opcional): Parâmetros de query.
            headers (dict | None, opcional): Headers adicionais.

        Returns:
            httpx.Response: Objeto de resposta.

        """
        return self._request("GET", url, params=params, headers=headers)

    def post(self, url: str, data: dict | None = None) -> httpx.Response:
        """Envia uma requisição POST para a API.

        Args:
            url (str): URL do endpoint (relativa ao base_url).
            data (dict | None, opcional): Corpo da requisição (JSON).

        Returns:
            httpx.Response: Objeto de resposta.

        """
        return self._request("POST", url, data=data)

    def put(self, url: str, data: dict | None = None) -> httpx.Response:
        """Envia uma requisição PUT para a API.

        Args:
            url (str): URL do endpoint (relativa ao base_url).
            data (dict | None, opcional): Corpo da requisição (JSON).

        Returns:
            httpx.Response: Objeto de resposta.

        """
        return self._request("PUT", url, data=data)

    def delete(self, url: str) -> httpx.Response:
        """Envia uma requisição DELETE para a API.

        Args:
            url (str): URL do endpoint (relativa ao base_url).

        Returns:
            httpx.Response: Objeto de resposta.

        """
        return self._request("DELETE", url)

    def patch(self, url: str, data: dict | None = None) -> httpx.Response:
        """Envia uma requisição PATCH para a API.

        Args:
            url (str): URL do endpoint (relativa ao base_url).
            data (dict | None, opcional): Corpo da requisição (JSON).

        Returns:
            httpx.Response: Objeto de resposta.

        """
        return self._request("PATCH", url, data=data)

    @classmethod
    def from_env(cls: Self) -> Self:
        """Instancia o ApiClient usando variáveis de ambiente.

        Espera que `API_BASE_URL` e `API_KEY` estejam definidas no ambiente.

        Returns:
            ApiClient: Instância do ApiClient com valores do ambiente.

        Raises:
            ValueError: Se `API_BASE_URL` ou `API_KEY` não estiverem definidos.

        """
        base_url = os.getenv("API_BASE_URL")
        api_key = os.getenv("API_KEY")
        if not base_url or not api_key:
            msg = "As variáveis de ambiente API_BASE_URL e API_KEY devem estar definidas"
            raise ValueError(msg)
        return cls(base_url=base_url, api_key=api_key)
