from typing import Self

import httpx
from redis import Redis
from redis.exceptions import RedisError


def get_redis_client(
    url: str | None = None,
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    decode_responses: bool = True,
) -> Redis:
    """Get a Redis client from a URL or a host, port, and database."""
    if url:
        client = Redis.from_url(url, decode_responses=decode_responses)
    else:
        client = Redis(host=host, port=port, db=db, decode_responses=decode_responses)
    if not client.ping():
        raise RedisError("Failed to connect to Redis")
    return client


DEFAULT_HTTP_TIMEOUT = 30.0


class ApiClient:
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_HTTP_TIMEOUT,
    ) -> None:
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
            return client.request(
                method, path, params=params, json=data, headers=headers
            )

    def get(
        self, url: str, params: dict | None = None, headers: dict | None = None
    ) -> httpx.Response:
        return self._request("GET", url, params=params, headers=headers)

    def post(self, url: str, data: dict | None = None) -> httpx.Response:
        return self._request("POST", url, data=data)

    def put(self, url: str, data: dict | None = None) -> httpx.Response:
        return self._request("PUT", url, data=data)

    def delete(self, url: str) -> httpx.Response:
        return self._request("DELETE", url)

    def patch(self, url: str, data: dict | None = None) -> httpx.Response:
        return self._request("PATCH", url, data=data)

    @classmethod
    def from_env(cls: Self) -> Self:
        import os

        base_url = os.getenv("API_BASE_URL")
        api_key = os.getenv("API_KEY")
        if not base_url or not api_key:
            raise ValueError("API_BASE_URL and API_KEY must be set")
        return cls(base_url=base_url, api_key=api_key)
