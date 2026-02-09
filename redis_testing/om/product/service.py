from logging import getLogger
from typing import Any

from redis import Redis

from redis_testing.om.utils import bootstrap
from redis_testing.utils import ApiClient, get_redis_client

from .manager import ProductOMObjects
from .model import ProductOM
from .utils import gerar_produtos_fake

logger = getLogger(__name__)


class Product:
    """Serviço para operações em produtos: bootstrap, popular com fakes, CRUD, get com fallback opcional para API."""

    def __init__(
        self,
        client: Redis | None = None,
        *,
        fallback_to_api: bool = False,
    ) -> None:
        """Serviço para operações em produtos.

        Args:
            client: Cliente Redis.
            fallback_to_api: Flag para fallback para API.

        """
        self._client = client or get_redis_client()
        bootstrap(self._client)
        self._model = ProductOM
        self._objects = ProductOM.objects
        self._fallback_to_api = fallback_to_api

    @property
    def fallback_to_api(self) -> bool:
        """Retorna o valor da flag de fallback para API."""
        return self._fallback_to_api

    @fallback_to_api.setter
    def fallback_to_api(self, value: bool) -> None:
        self._fallback_to_api = value

    @property
    def api_client(self) -> ApiClient:
        """Retorna o cliente API usando variáveis de ambiente."""
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

    @property
    def model(self) -> ProductOM:
        """Retorna o modelo do produto."""
        return self._model

    @property
    def objects(self) -> ProductOMObjects:
        """Retorna o manager dos produtos."""
        return self._objects

    def populate(
        self,
        quantidade: int,
        id_prefix: str = "prod",
        seed: int | None = None,
    ) -> int:
        """Popula o Redis com `quantidade` produtos falsos.

        Args:
            quantidade: Número de produtos a criar.
            id_prefix: Prefixo do id (ex.: "prod" -> prod-1, prod-2, ...).
            seed: Seed opcional para reprodutibilidade.

        Returns:
            Quantidade de produtos efetivamente criados (pode ser menor se algum pk já existir).

        """
        criados = 0
        for data in gerar_produtos_fake(quantidade, id_prefix=id_prefix, seed=seed):
            try:
                self._objects.create(
                    product_id=data["id"],
                    name=data["name"],
                    description=data["description"],
                    category=data["category"],
                    price=data["price"],
                )
                criados += 1
            except Exception:
                logger.warning("Erro ao criar produto: %s", data)
        return criados

    def create_product(
        self,
        product_id: str,
        name: str,
        description: str,
        category: str,
        price: float = 0.0,
    ) -> ProductOM:
        """Cria um produto.

        Args:
            product_id: Chave primária do produto.
            name: Nome do produto.
            description: Descrição do produto.
            category: Categoria do produto.
            price: Preço do produto.

        """
        return self._objects.create(
            product_id=product_id,
            name=name,
            description=description,
            category=category,
            price=price,
        )

    def get(
        self,
        pk: str,
        *,
        fallback_to_api: bool | None = None,
        ttl_seconds: int | None = None,
    ) -> ProductOM | None:
        """Busca por chave primária. Se fallback_to_api (ou self.fallback_to_api), em miss busca na API e persiste no cache.

        Args:
            pk: Chave primária do produto.
            fallback_to_api: Flag para fallback para API.
            ttl_seconds: Tempo de vida do cache.

        Returns:
            Produto encontrado ou None.

        """
        existing = self._objects.get(pk)
        if existing is not None:
            return existing

        use_fallback = fallback_to_api if fallback_to_api is not None else self._fallback_to_api
        if not use_fallback:
            return None

        try:
            response = self.api_client.get(f"/products/{pk}")
        except Exception:
            logger.exception("Fallback API GET /products/%s failed", pk)
            return None
        if not response.is_success:
            return None
        data = response.json()
        inst = self._objects.create(
            product_id=data.get("id", pk),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            price=float(data.get("price", 0.0)),
        )
        if ttl_seconds is not None:
            inst.expire(ttl_seconds)
        return inst

    def get_by_category(self, category: str) -> list[ProductOM]:
        """Busca por categoria.

        Args:
            category: Categoria do produto.

        Returns:
            Lista de produtos encontrados.

        """
        return self._objects.find_by_category(category)

    def search_by_name(self, query: str, limit: int = 100) -> list[ProductOM]:
        """Busca full-text no nome.

        Args:
            query: Query de busca.
            limit: Limite de resultados.

        Returns:
            Lista de produtos encontrados.

        """
        return self._objects.find_by_name(query, limit=limit)

    def list_products(
        self,
        offset: int = 0,
        limit: int = 10,
        *,
        sort_by_price_asc: bool = True,
    ) -> list[ProductOM]:
        """Lista com paginação e ordenação por preço.

        Args:
            offset: Offset.
            limit: Limite.
            sort_by_price_asc: Ordenar por preço ascendente.

        Returns:
            Lista de produtos encontrados.

        """
        return self._objects.list_all(
            offset=offset,
            limit=limit,
            sort_by_price_asc=sort_by_price_asc,
        )

    def count(self) -> int:
        """Total de produtos no índice.

        Returns:
            Total de produtos no índice.

        """
        return self._objects.count()

    def delete_product(self, pk: str) -> bool:
        """Remove por chave primária.

        Args:
            pk: Chave primária do produto.

        Returns:
            True se o produto foi removido, False caso contrário.

        """
        return self._objects.delete(pk)

    def get_or_create(
        self,
        product_id: str,
        defaults: dict[str, Any] | None = None,
    ) -> tuple[ProductOM, bool]:
        """Busca por pk; se não existir, cria com defaults. Retorna (instância, criado).

        Args:
            product_id: Chave primária do produto.
            defaults: Defaults para o produto.

        Returns:
            Tuple[ProductOM, bool]: Tuple com a instância do produto e se foi criado.

        """
        defaults = defaults or {}
        existing = self._objects.get(product_id)
        if existing is not None:
            return (existing, False)
        created = self._objects.create(
            product_id=product_id,
            name=defaults.get("name", ""),
            description=defaults.get("description", ""),
            category=defaults.get("category", ""),
            price=defaults.get("price", 0.0),
        )
        return (created, True)

    def update_or_create(
        self,
        product_id: str,
        defaults: dict[str, Any] | None = None,
    ) -> tuple[ProductOM, bool]:
        """Busca por pk.

        Se existir, atualiza com defaults; senão, cria. Retorna (instância, criado).

        Args:
            product_id: Chave primária do produto.
            defaults: Defaults para o produto.

        Returns:
            Tuple[ProductOM, bool]: Tuple com a instância do produto e se foi criado.

        """
        defaults = defaults or {}
        existing = self._objects.get(product_id)
        if existing is not None:
            update_kwargs = {
                k: v
                for k, v in defaults.items()
                if k in {"name", "description", "category", "price"}
            }
            if update_kwargs:
                existing.update(**update_kwargs)
            return (existing, False)
        created = self._objects.create(
            product_id=product_id,
            name=defaults.get("name", ""),
            description=defaults.get("description", ""),
            category=defaults.get("category", ""),
            price=defaults.get("price", 0.0),
        )
        return (created, True)


product = Product()
