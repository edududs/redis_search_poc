# pyright: reportMissingImports=false
# ruff: noqa: TC002
from __future__ import annotations

import json
from functools import wraps
from logging import getLogger
from typing import Any, Callable, overload

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from redis import Redis

from display import print_redis_error

logger = getLogger(__name__)


def handle_redis_error(default: Any = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator para tratamento padronizado de erros Redis."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                prefix = getattr(self, "hash_prefix", "unknown")
                print_redis_error(func.__name__, prefix, e)
                return default

        return wrapper

    return decorator


class RedisCache[T](BaseModel):
    """Cache Unificado SOTA (Redis 8 + Pydantic V2)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    hash_prefix: str
    index_name: str | None = None
    indexed_fields: list[str] = Field(default_factory=list)
    ttl_seconds: int = 3600
    use_json_storage: bool = Field(default=False)

    _index_ensured: bool = PrivateAttr(default=False)
    client: Redis = Field(exclude=True)

    def _get_client(self) -> Redis:
        return self.client

    def _build_key(self, key: Any) -> str:
        return f"{self.hash_prefix}{key}"

    def _prepare_mapping(self, key: str | int, data: T) -> dict[Any, Any]:
        """Prepara dados para hash, normalizando para strings."""
        if isinstance(data, BaseModel):
            mapping = data.model_dump(mode="json")
        elif isinstance(data, dict):
            mapping = data
        else:
            # Mapeamento simples (key_field -> value_field)
            val_field = self.indexed_fields[1] if len(self.indexed_fields) > 1 else "value"
            key_field = self.indexed_fields[0] if self.indexed_fields else "key"
            mapping = {key_field: str(key), val_field: str(data)}

        return {k: str(v) for k, v in mapping.items() if v is not None}

    def _parse_output(self, data: Any, model_type: type[T] | None) -> T | Any:
        """Centraliza a lógica de desserialização e reconstrução (DRY)."""
        if data is None:
            return None

        # Converter bytes/str JSON para dict/list se necessário
        if isinstance(data, (str, bytes)):
            try:
                if isinstance(data, bytes):
                    data = data.decode()
                # Tenta decodificar se parecer JSON estruturado (apenas se use_json_storage ou se identificou que é json)
                # Porém, para manter KISS: se model_type existe, deixe o pydantic tratar.
                # Se não, e for string JSON, convertemos.
                if not model_type and data.startswith(("{", "[")):
                    data = json.loads(data)
            except (json.JSONDecodeError, AttributeError):
                pass  # Mantém como string raw

        # Reconstrução Pydantic
        if model_type and issubclass(model_type, BaseModel):
            if isinstance(data, (str, bytes)):
                return model_type.model_validate_json(data)
            return model_type.model_validate(data)

        # Fallback para valor simples (ex: get("123") -> "Produto X")
        if isinstance(data, dict) and not model_type and self.indexed_fields:
            target = self.indexed_fields[1] if len(self.indexed_fields) > 1 else "value"
            return data.get(target, data)

        return data

    @handle_redis_error(default=None)
    def ensure_index(self) -> None:
        """Cria índice RediSearch de forma idempotente."""
        if self._index_ensured or not (self.index_name and self.indexed_fields):
            return

        from redis.commands.search.field import TagField
        from redis.commands.search.index_definition import IndexDefinition, IndexType
        from redis.exceptions import ResponseError

        r = self._get_client()
        ft = r.ft(self.index_name)

        try:
            ft.info()
            self._index_ensured = True
            return
        except ResponseError:
            # Índice desconhecido, prossegue para criação
            pass

        schema = [TagField(f) for f in self.indexed_fields]
        try:
            ft.create_index(
                fields=schema,
                definition=IndexDefinition(prefix=[self.hash_prefix], index_type=IndexType.HASH),
            )
            logger.info("Índice '%s' criado.", self.index_name)
        except ResponseError as e:
            if "Index already exists" not in str(e):
                raise

        self._index_ensured = True

    @handle_redis_error(default=None)
    def save(self, key: str | int, data: T) -> None:
        """Salva registro no cache (JSON ou Hash)."""
        r = self._get_client()
        hash_key = self._build_key(key)

        if self.use_json_storage:
            payload = data.model_dump_json() if isinstance(data, BaseModel) else json.dumps(data)
            r.setex(hash_key, self.ttl_seconds, payload)
            return

        mapping = self._prepare_mapping(key, data)
        if not mapping:
            r.setex(hash_key, self.ttl_seconds, "{}")  # Fallback para vazio
            return

        r.hset(hash_key, mapping=mapping)
        r.expire(hash_key, self.ttl_seconds)

    @overload
    def get(self, key: str | int, model_type: type[T]) -> T | None: ...
    @overload
    def get(self, key: str | int, model_type: None = None) -> Any: ...

    @handle_redis_error(default=None)
    def get(self, key: str | int, model_type: type[T] | None = None) -> T | Any:
        """Busca e desserializa dado do cache."""
        r = self._get_client()
        hash_key = self._build_key(key)

        # 1. Tenta buscar direto (funciona para JSON storage ou se for string pura)
        # Se use_json_storage=True, é string direta.
        if self.use_json_storage:
            return self._parse_output(r.get(hash_key), model_type)

        # 2. Verifica tipo para decidir estratégia (Hash vs String/JSON legado)
        k_type = r.type(hash_key)
        type_str = k_type.decode() if isinstance(k_type, bytes) else k_type

        raw_data: Any = None
        if type_str == "hash":
            raw = r.hgetall(hash_key)
            if raw:
                # Decode dict keys/values
                raw_data = {
                    (k.decode() if isinstance(k, bytes) else k): (
                        v.decode() if isinstance(v, bytes) else v
                    )
                    for k, v in raw.items()
                }
        elif type_str == "string":
            raw_data = r.get(hash_key)

        return self._parse_output(raw_data, model_type)

    @handle_redis_error(default=None)
    def find_one(self, field: str, value: Any, model_type: type[T] | None = None) -> T | None:
        """Busca reversa via RediSearch."""
        if not self.index_name:
            return None

        self.ensure_index()
        r = self._get_client()
        from redis.commands.search.query import Query

        # Busca exata com TagField: @campo:{valor}
        q = Query(f"@{field}:{{{value}}}").paging(0, 1)
        res = r.ft(self.index_name).search(q)

        if not res.docs:
            return None

        # Extrai dados do documento RediSearch
        doc = res.docs[0]
        redis_key = doc.id

        # Extrai o id do modelo removendo o hash_prefix da chave do Redis
        model_id = redis_key
        if redis_key.startswith(self.hash_prefix):
            model_id = redis_key[len(self.hash_prefix) :]

        # Mantém todos os dados do RediSearch, garantindo que o id seja o do modelo
        data = dict(doc.__dict__)
        data["id"] = model_id

        return self._parse_output(data, model_type)

    @handle_redis_error(default=False)
    def delete(self, key: str | int) -> bool:
        """Remove registro."""
        return bool(self._get_client().delete(self._build_key(key)))

    @handle_redis_error(default=False)
    def exists(self, key: str | int) -> bool:
        """Verifica existência."""
        return bool(self._get_client().exists(self._build_key(key)))

    @handle_redis_error(default=0)
    def bulk_save(self, items: list[tuple[str | int, T]]) -> int:
        """Guarda múltiplos itens via pipeline."""
        if not items:
            return 0

        pipe = self._get_client().pipeline()
        count = 0

        for key, data in items:
            hash_key = self._build_key(key)
            mapping = self._prepare_mapping(key, data)
            pipe.hset(hash_key, mapping=mapping)
            pipe.expire(hash_key, self.ttl_seconds)
            count += 1

        pipe.execute()
        return count
