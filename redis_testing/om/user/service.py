from logging import getLogger
from typing import TYPE_CHECKING, Any

from redis import Redis

from redis_testing.om import bootstrap
from redis_testing.utils import ApiClient, get_redis_client

from .model import UserOM
from .utils import gerar_usuarios_fake

logger = getLogger(__name__)
if TYPE_CHECKING:
    from .manager import UserOMObjects

DEFAULT_TTL_SECONDS = 60 * 3


class User:
    """Serviço para operações em usuários.

    Features:
        Bootstrap
        Popular com fakes
        CRUD
        Get com fallback opcional para API
    """

    def __init__(
        self,
        client: Redis | None = None,
        *,
        fallback_to_api: bool = False,
    ) -> None:
        """Serviço para operações em usuários.

        Args:
            client: Cliente Redis.
            fallback_to_api: Flag para fallback para API.

        """
        self._client = client or get_redis_client()
        bootstrap(self._client)
        self._model = UserOM
        self._objects = UserOM.objects
        self._fallback_to_api = fallback_to_api

    @property
    def fallback_to_api(self) -> bool:
        """Retorna o valor da flag de fallback para API."""
        return self._fallback_to_api

    @fallback_to_api.setter
    def fallback_to_api(self, value: bool) -> None:
        """Define o valor da flag de fallback para API."""
        self._fallback_to_api = value

    @property
    def model(self) -> UserOM:
        """Retorna o modelo do usuário."""
        return self._model

    @property
    def objects(self) -> "UserOMObjects":
        """Retorna o manager dos usuários."""
        return self._objects

    @property
    def api_client(self) -> ApiClient:
        """Retorna o cliente API."""
        return ApiClient.from_env()

    def clear(self) -> int:
        """Remove todos os documentos deste modelo.

        Returns:
            Quantidade de documentos apagados.

        """
        meta = self._model.Meta
        pattern = f"{meta.global_key_prefix}:{meta.model_key_prefix}:*"
        keys = self._client.keys(pattern)
        if keys:
            self._client.delete(*keys)
        return len(keys)

    def populate(
        self,
        quantidade: int,
        id_prefix: str = "fake",
        seed: int | None = None,
    ) -> int:
        """Popula o Redis com `quantidade` usuários falsos (email e CPF únicos no lote).

        Args:
            quantidade: Número de usuários a criar.
            id_prefix: Prefixo do id (ex.: "fake" -> fake-1, fake-2, ...).
            seed: Seed opcional para reprodutibilidade.

        Returns:
            Quantidade de usuários efetivamente criados (pode ser menor se algum pk já existir).

        """
        criados = 0
        for data in gerar_usuarios_fake(quantidade, id_prefix=id_prefix, seed=seed):
            try:
                self._objects.create(
                    user_id=data["id"],
                    name=data["name"],
                    email=data["email"],
                    cpf=data["cpf"],
                    age=data["age"],
                    weight=data["weight"],
                    height=data["height"],
                )
                criados += 1
            except Exception:
                logger.warning("Erro ao criar usuário: %s", data)
        return criados

    def create_user(
        self,
        user_id: str,
        name: str,
        email: str,
        cpf: str,
        age: int = 0,
        weight: float = 0.0,
        height: float = 0.0,
        *,
        ensure_unique_email: bool = True,
        ensure_unique_cpf: bool = True,
    ) -> UserOM:
        """Cria um usuário. Opcionalmente garante que email e/ou CPF não existam (único).

        Se ensure_unique_email ou ensure_unique_cpf for True e já existir registro
        com esse email/cpf, levanta ValueError. Use isso para testar “campo único”.

        Args:
            user_id: Chave primária do usuário.
            name: Nome do usuário.
            email: Email do usuário.
            cpf: CPF do usuário.
            age: Idade do usuário.
            weight: Peso do usuário.
            height: Altura do usuário.
            ensure_unique_email: Garantir que o email seja único.
            ensure_unique_cpf: Garantir que o CPF seja único.

        Returns:
            UserOM: O usuário criado.

        Raises:
            ValueError: Se o email ou CPF já estiver cadastrado, dependendo das opções de unicidade.

        """
        if ensure_unique_email:
            existentes = self._objects.find_by_email(email)
            if existentes:
                msg = f"Email já cadastrado: {email}"
                raise ValueError(msg)
        if ensure_unique_cpf:
            existente = self._objects.find_by_cpf(cpf)
            if existente is not None:
                msg = f"CPF já cadastrado: {cpf}"
                raise ValueError(msg)

        return self._objects.create(
            user_id=user_id,
            name=name,
            email=email,
            cpf=cpf,
            age=age,
            weight=weight,
            height=height,
        )

    def get(
        self,
        pk: str,
        *,
        fallback_to_api: bool | None = None,
        ttl_seconds: int | None = None,
    ) -> UserOM | None:
        """Busca por chave primária.

        Se `fallback_to_api` (ou `self.fallback_to_api`), em miss, busca na API e persiste no cache.

        Args:
            pk: Chave primária do usuário.
            fallback_to_api: Flag para fallback para API.
            ttl_seconds: Tempo de vida do cache.

        Returns:
            Usuário encontrado ou None.

        """
        existing = self._objects.get(pk)
        if existing is not None:
            return existing

        use_fallback = fallback_to_api if fallback_to_api is not None else self._fallback_to_api
        if not use_fallback:
            return None

        try:
            response = self.api_client.get(f"/users/{pk}")
        except Exception:
            logger.exception("Fallback API GET /users/%s failed", pk)
            return None
        if not response.is_success:
            return None
        data = response.json()
        inst = self._objects.create(
            user_id=data.get("id", pk),
            name=data.get("name", ""),
            email=data.get("email", ""),
            cpf=data.get("cpf", ""),
            age=int(data.get("age", 0)),
            weight=float(data.get("weight", 0.0)),
            height=float(data.get("height", 0.0)),
        )
        inst.expire(ttl_seconds or DEFAULT_TTL_SECONDS)
        return inst

    def get_by_email(self, email: str) -> list[UserOM]:
        """Busca por email.

        Args:
            email: Email do usuário.

        Returns:
            Lista de usuários encontrados.

        """
        return self._objects.find_by_email(email)

    def get_by_cpf(self, cpf: str) -> UserOM | None:
        """Busca por CPF. Retorna o primeiro ou None.

        Args:
            cpf: CPF do usuário.

        Returns:
            Usuário encontrado ou None.

        """
        return self._objects.find_by_cpf(cpf)

    def search_by_name(self, query: str, limit: int = 100) -> list[UserOM]:
        """Busca full-text no nome.

        Args:
            query: Query de busca.
            limit: Limite de resultados.

        Returns:
            Lista de usuários encontrados.

        """
        return self._objects.find_by_name(query, limit=limit)

    def list_users(
        self,
        offset: int = 0,
        limit: int = 10,
        *,
        sort_by_age_asc: bool = True,
    ) -> list[UserOM]:
        """Lista com paginação e ordenação por idade.

        Args:
            offset: Offset.
            limit: Limite.
            sort_by_age_asc: Ordenar por idade ascendente.

        Returns:
            Lista de usuários encontrados.

        """
        return self._objects.list_all(
            offset=offset,
            limit=limit,
            sort_by_age_asc=sort_by_age_asc,
        )

    def count(self) -> int:
        """Total de usuários no índice.

        Returns:
            Total de usuários no índice.

        """
        return self._objects.count()

    def delete_user(self, pk: str) -> bool:
        """Remove por chave primária.

        Args:
            pk: Chave primária do usuário.

        Returns:
            True se o usuário foi removido, False caso contrário.

        """
        return self._objects.delete(pk)

    def get_or_create(
        self,
        user_id: str,
        defaults: dict[str, Any] | None = None,
    ) -> tuple[UserOM, bool]:
        """Busca por pk; se não existir, cria com defaults. Retorna (instância, criado).

        Args:
            user_id: Chave primária do usuário.
            defaults: Defaults para o usuário.

        Returns:
            Tuple[UserOM, bool]: Tuple com a instância do usuário e se foi criado.

        """
        defaults = defaults or {}
        existing = self._objects.get(user_id)
        if existing is not None:
            return (existing, False)
        created = self._objects.create(
            user_id=user_id,
            name=defaults.get("name", ""),
            email=defaults.get("email", ""),
            cpf=defaults.get("cpf", ""),
            age=defaults.get("age", 0),
            weight=defaults.get("weight", 0.0),
            height=defaults.get("height", 0.0),
        )
        return (created, True)

    def update_or_create(
        self,
        user_id: str,
        defaults: dict[str, Any] | None = None,
    ) -> tuple[UserOM, bool]:
        """Busca por pk.

        Se existir, atualiza com defaults; senão, cria. Retorna (instância, criado).

        Args:
            user_id: Chave primária do usuário.
            defaults: Defaults para o usuário.

        Returns:
            (UserOM, bool): Tuple com a instância do usuário e se foi criado.

        """
        defaults = defaults or {}
        existing = self._objects.get(user_id)
        if existing is not None:
            update_kwargs = {
                k: v
                for k, v in defaults.items()
                if k in {"name", "email", "cpf", "age", "weight", "height"}
            }
            if update_kwargs:
                existing.update(**update_kwargs)
            return (existing, False)
        created = self._objects.create(
            user_id=user_id,
            name=defaults.get("name", ""),
            email=defaults.get("email", ""),
            cpf=defaults.get("cpf", ""),
            age=defaults.get("age", 0),
            weight=defaults.get("weight", 0.0),
            height=defaults.get("height", 0.0),
        )
        return (created, True)


user = User()
