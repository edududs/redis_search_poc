"""Exemplos completos de uso: HashModel, JsonModel e RedisCache genérico."""

from logging import getLogger

from pydantic import BaseModel
from rich.console import Console

from display import ExampleDisplayer
from redis_testing.cache import RedisCache
from redis_testing.utils import get_redis_client

from .utils import bootstrap

logger = getLogger(__name__)


class HashModelExample:
    """Demonstra uso do HashModel (UserOM) - armazenamento como Hash Redis."""

    def __init__(self, console: Console) -> None:
        self._displayer = ExampleDisplayer(console)
        from .user import User

        self.service = User()

    def run(self) -> None:
        """Executa todos os exemplos de HashModel."""
        self._displayer.example_title_panel(
            "Redis OM - HashModel", "HashModel Example (UserOM)", border_style="blue"
        )

        self._create_users()
        self._get_by_primary_key()
        self._find_by_fields()
        self._list_with_pagination()
        self._update_and_delete()

    def _create_users(self) -> None:
        """Cria usuários usando HashModel (idempotente)."""
        self._displayer.section_title("1. Criando usuários (HashModel)")

        user1, created1 = self.service.get_or_create(
            "hash-user-1",
            defaults={
                "name": "Alice Hash",
                "email": "alice.hash@example.com",
                "cpf": "111.222.333-44",
                "age": 28,
                "weight": 58.5,
                "height": 1.65,
            },
        )
        self._displayer.creation_result(user1.id, user1.name, created1)

        user2, created2 = self.service.get_or_create(
            "hash-user-2",
            defaults={
                "name": "Bob Hash",
                "email": "bob.hash@example.com",
                "cpf": "555.666.777-88",
                "age": 35,
                "weight": 82.0,
                "height": 1.78,
            },
        )
        self._displayer.creation_result(user2.id, user2.name, created2)

    def _get_by_primary_key(self) -> None:
        """Busca por chave primária."""
        self._displayer.section_title("2. Busca por chave primária")

        user = self.service.get("hash-user-1")
        self._displayer.get_result("hash-user-1", user)

    def _find_by_fields(self) -> None:
        """Busca por campos indexados."""
        self._displayer.section_title("3. Busca por campos (email, CPF, nome)")

        by_email = self.service.get_by_email("alice.hash@example.com")
        self._displayer.find_result("find_by_email", "", by_email, border_style="blue")

        by_cpf = self.service.get_by_cpf("555.666.777-88")
        self._displayer.find_result("find_by_cpf", "", by_cpf, border_style="blue")

        by_name = self.service.search_by_name("Alice")
        if by_name:
            self._displayer.find_result("search_by_name", "Alice", by_name, border_style="blue")

    def _list_with_pagination(self) -> None:
        """Lista com paginação e ordenação."""
        self._displayer.section_title("4. Listagem com paginação e ordenação")

        users = self.service.list_users(offset=0, limit=5, sort_by_age_asc=True)
        rows = [[u.id, u.name, u.email, str(u.age)] for u in users]
        self._displayer.custom_table(
            "4. Listagem com paginação e ordenação",
            columns=["ID", "Nome", "Email", "Idade"],
            rows=rows,
            border_style="blue",
        )

    def _update_and_delete(self) -> None:
        """Atualiza e deleta registros."""
        self._displayer.section_title("5. Atualização e deleção")

        user, created = self.service.get_or_create(
            "hash-user-3",
            defaults={
                "name": "Charlie Hash",
                "email": "charlie@example.com",
                "cpf": "999.888.777-66",
            },
        )
        self._displayer.operation_result("get_or_create", user.id, f"(criado={created})")

        user, updated = self.service.update_or_create(
            "hash-user-3",
            defaults={"age": 42},
        )
        self._displayer.operation_result(
            "update_or_create", user.id, f"idade={user.age} (criado={updated})"
        )

        deleted = self.service.delete_user("hash-user-3")
        self._displayer.operation_result("delete", "hash-user-3", "", success=deleted)


class JsonModelExample:
    """Demonstra uso do JsonModel (ProductOM) - armazenamento como JSON Redis."""

    def __init__(self, console: Console) -> None:
        self._displayer = ExampleDisplayer(console)
        from .product import Product

        self.service = Product()

    def run(self) -> None:
        """Executa todos os exemplos de JsonModel."""
        self._displayer.example_title_panel(
            "Redis OM - JsonModel", "JsonModel Example (ProductOM)", border_style="green"
        )

        self._create_products()
        self._get_by_primary_key()
        self._find_by_fields()
        self._list_with_pagination()
        self._update_and_delete()

    def _create_products(self) -> None:
        """Cria produtos usando JsonModel (idempotente)."""
        self._displayer.section_title("1. Criando produtos (JsonModel)")

        prod1, created1 = self.service.get_or_create(
            "json-prod-1",
            defaults={
                "name": "Notebook Gamer JSON",
                "description": "Notebook com GPU dedicada para jogos",
                "category": "eletrônicos",
                "price": 5499.90,
            },
        )
        self._displayer.creation_result(prod1.id, prod1.name, created1, price=prod1.price)

        prod2, created2 = self.service.get_or_create(
            "json-prod-2",
            defaults={
                "name": "Teclado Mecânico JSON",
                "description": "Teclado mecânico RGB switches azuis",
                "category": "periféricos",
                "price": 399.90,
            },
        )
        self._displayer.creation_result(prod2.id, prod2.name, created2, price=prod2.price)

    def _get_by_primary_key(self) -> None:
        """Busca por chave primária."""
        self._displayer.section_title("2. Busca por chave primária")

        product = self.service.get("json-prod-1")
        self._displayer.get_result("json-prod-1", product)

    def _find_by_fields(self) -> None:
        """Busca por campos indexados."""
        self._displayer.section_title("3. Busca por campos (categoria, nome full-text)")

        by_category = self.service.get_by_category("periféricos")
        self._displayer.find_result("find_by_category", "periféricos", by_category, border_style="green")

        by_name = self.service.search_by_name("Gamer")
        self._displayer.find_result("search_by_name", "Gamer", by_name, border_style="green")

    def _list_with_pagination(self) -> None:
        """Lista com paginação e ordenação."""
        self._displayer.section_title("4. Listagem com paginação e ordenação")

        products = self.service.list_products(offset=0, limit=5, sort_by_price_asc=True)
        rows = [[p.id, p.name, p.category, f"R$ {p.price:.2f}"] for p in products]
        self._displayer.custom_table(
            "4. Listagem com paginação e ordenação",
            columns=["ID", "Nome", "Categoria", "Preço"],
            rows=rows,
            border_style="green",
        )

    def _update_and_delete(self) -> None:
        """Atualiza e deleta registros."""
        self._displayer.section_title("5. Atualização e deleção")

        product, created = self.service.get_or_create(
            "json-prod-3",
            defaults={
                "name": "Mouse Gamer JSON",
                "description": "Mouse gamer 16000 DPI",
                "category": "periféricos",
                "price": 249.90,
            },
        )
        self._displayer.operation_result("get_or_create", product.id, f"(criado={created})")

        product, updated = self.service.update_or_create(
            "json-prod-3",
            defaults={"price": 199.90},
        )
        self._displayer.operation_result(
            "update_or_create", product.id, f"preço=R$ {product.price:.2f} (criado={updated})"
        )

        deleted = self.service.delete_product("json-prod-3")
        self._displayer.operation_result("delete", "json-prod-3", "", success=deleted)


class CacheSimpleExample:
    """Demonstra RedisCache com valores simples (strings, dicts)."""

    def __init__(self, console: Console) -> None:
        self._displayer = ExampleDisplayer(console)
        self.client = get_redis_client()
        self.cache = RedisCache[str](
            client=self.client,
            hash_prefix="cache:simple:",
            ttl_seconds=300,
        )

    def run(self) -> None:
        """Executa exemplos de cache simples."""
        self._displayer.example_title_panel(
            "Cache Genérico", "RedisCache - Valores Simples", border_style="yellow"
        )

        self._string_cache()
        self._dict_cache()

    def _string_cache(self) -> None:
        """Cache de strings simples."""
        self._displayer.section_title("1. Cache de strings")

        self.cache.save("chave1", "valor1")
        self.cache.save("chave2", "valor2")

        valor = self.cache.get("chave1")
        self._displayer.cache_get("chave1", valor)

        existe = self.cache.exists("chave1")
        self._displayer.cache_exists("chave1", existe)

        self.cache.delete("chave1")
        self._displayer.cache_delete("chave1")

    def _dict_cache(self) -> None:
        """Cache de dicionários."""
        self._displayer.section_title("2. Cache de dicionários")

        dict_cache = RedisCache[dict](
            client=self.client,
            hash_prefix="cache:dict:",
            ttl_seconds=600,
        )

        dados = {
            "usuario": "alice",
            "email": "alice@example.com",
            "idade": 30,
        }

        dict_cache.save("user-1", dados)
        dados_recuperados = dict_cache.get("user-1")
        self._displayer.cache_get("user-1", dados_recuperados)


class CacheModelExample:
    """Demonstra RedisCache com modelos Pydantic."""

    def __init__(self, console: Console) -> None:
        self._displayer = ExampleDisplayer(console)
        self.client = get_redis_client()

    def run(self) -> None:
        """Executa exemplos de cache com modelos."""
        self._displayer.example_title_panel(
            "Cache Genérico", "RedisCache - Modelos Pydantic", border_style="magenta"
        )

        self._json_storage_example()
        self._hash_storage_example()
        self._indexed_search_example()

    def _json_storage_example(self) -> None:
        """Cache com JSON storage."""
        self._displayer.section_title("1. JSON Storage (use_json_storage=True)")

        class Produto(BaseModel):
            id: str
            nome: str
            preco: float
            categoria: str

        cache = RedisCache[Produto](
            client=self.client,
            hash_prefix="cache:json:",
            ttl_seconds=3600,
            use_json_storage=True,
        )

        produto = Produto(
            id="prod-1",
            nome="Notebook",
            preco=2999.90,
            categoria="eletrônicos",
        )

        cache.save("prod-1", produto)
        produto_recuperado = cache.get("prod-1", Produto)
        if produto_recuperado:
            self._displayer.get_result("prod-1", produto_recuperado)

    def _hash_storage_example(self) -> None:
        """Cache com Hash storage."""
        self._displayer.section_title("2. Hash Storage (use_json_storage=False)")

        class Produto(BaseModel):
            id: str
            nome: str
            preco: float
            categoria: str

        cache = RedisCache[Produto](
            client=self.client,
            hash_prefix="cache:hash:",
            ttl_seconds=3600,
            use_json_storage=False,
        )

        produto = Produto(
            id="prod-2",
            nome="Teclado",
            preco=399.90,
            categoria="periféricos",
        )

        cache.save("prod-2", produto)
        produto_recuperado = cache.get("prod-2", Produto)
        if produto_recuperado:
            self._displayer.get_result("prod-2", produto_recuperado)

    def _indexed_search_example(self) -> None:
        """Cache com índices RediSearch para busca reversa."""
        self._displayer.section_title("3. Busca reversa com RediSearch")

        class Produto(BaseModel):
            id: str
            nome: str
            preco: float
            categoria: str

        cache = RedisCache[Produto](
            client=self.client,
            hash_prefix="cache:idx:",
            index_name="idx_produtos_cache",
            indexed_fields=["categoria", "nome"],
            ttl_seconds=3600,
            use_json_storage=False,
        )

        cache.ensure_index()

        produtos = [
            Produto(id="prod-3", nome="Notebook Gamer", preco=4999.90, categoria="eletrônicos"),
            Produto(id="prod-4", nome="Teclado Mecânico", preco=399.90, categoria="periféricos"),
        ]

        for p in produtos:
            cache.save(p.id, p)

        encontrado = cache.find_one("categoria", "eletrônicos", Produto)
        self._displayer.cache_find_one("categoria", "eletrônicos", encontrado)

        # Bulk save
        produtos_bulk = [
            ("prod-5", Produto(id="prod-5", nome="Mouse", preco=199.90, categoria="periféricos")),
            (
                "prod-6",
                Produto(id="prod-6", nome="Monitor", preco=1299.90, categoria="eletrônicos"),
            ),
        ]
        salvos = cache.bulk_save(produtos_bulk)
        self._displayer.cache_bulk_save(salvos, entity_name="produtos")


class ExampleRunner:
    """Orquestra a execução de todos os exemplos."""

    def __init__(self, console: Console | None = None) -> None:
        console = console or Console()
        self._displayer = ExampleDisplayer(console)
        self.client = get_redis_client()
        bootstrap(self.client)

    def run_all(self, clear: bool = False) -> None:
        """Executa todos os exemplos em sequência."""
        self._displayer.example_title_panel(
            "Redis Testing Examples",
            "Exemplos Completos: HashModel, JsonModel e RedisCache",
            border_style="bold cyan",
        )

        hash_example = HashModelExample(self._displayer.console)
        hash_example.run()

        self._displayer.console.print()

        json_example = JsonModelExample(self._displayer.console)
        json_example.run()

        self._displayer.console.print()

        cache_simple = CacheSimpleExample(self._displayer.console)
        cache_simple.run()

        self._displayer.console.print()

        cache_model = CacheModelExample(self._displayer.console)
        cache_model.run()

        self._displayer.success_panel("Todos os exemplos executados com sucesso!")

        if clear:
            self._clear_all()

    def _clear_all(self) -> None:
        """Limpa todos os dados criados pelos exemplos (idempotente)."""
        self._displayer.cleanup_section()

        # Limpar HashModel (UserOM)
        from .user import User

        user_service = User(client=self.client)
        n_users = user_service.clear()
        if n_users:
            self._displayer.cleanup_result(n_users, "usuários (HashModel)")

        # Limpar JsonModel (ProductOM)
        from .product import Product

        product_service = Product(client=self.client)
        n_products = product_service.clear()
        if n_products:
            self._displayer.cleanup_result(n_products, "produtos (JsonModel)")

        # Limpar caches genéricos
        patterns = [
            "cache:simple:*",
            "cache:dict:*",
            "cache:json:*",
            "cache:hash:*",
            "cache:idx:*",
        ]

        total_deleted = 0
        for pattern in patterns:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                total_deleted += deleted

        if total_deleted:
            self._displayer.cleanup_result(total_deleted, "chaves de cache genérico")

        # Limpar índices RediSearch criados pelos exemplos
        try:
            from redis.exceptions import ResponseError

            index_name = "idx_produtos_cache"
            ft = self.client.ft(index_name)
            try:
                ft.dropindex(delete_documents=True)
                self._displayer.cleanup_index(index_name)
            except ResponseError:
                # Índice não existe, ok - exemplo é idempotente
                pass
        except Exception as e:
            # Ignora erros na limpeza de índices (pode não existir)
            logger.debug("Erro ao limpar índice: %s", e)

        self._displayer.cleanup_complete()


def run_examples(clear: bool = False) -> None:
    """Entry point para executar os exemplos."""
    runner = ExampleRunner()
    runner.run_all(clear=clear)
