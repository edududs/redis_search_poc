"""CLI para popular Redis (usuários/produtos) e testar fallback para a API."""

import logging
import os
import secrets
import time
from pathlib import Path
from string import digits
from typing import Any

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from display import SampleDisplayer
from redis_testing.om import Product, User
from redis_testing.utils import ApiClient

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent
_DEFAULT_DB_PATH = _PROJECT_ROOT / "api" / "fallback.db"

load_dotenv(_PROJECT_ROOT / ".env")

POPULATE_USERS = 300
POPULATE_PRODUCTS = 300


def _env(key: str, default: str = "") -> str:
    """Obtém o valor da variável de ambiente."""
    return os.getenv(key, default)


def _shutdown_api(console: Console) -> bool:
    """Chama POST /internal/shutdown na API. Retorna True se a chamada foi feita com sucesso."""
    base_url = _env("API_BASE_URL")
    api_key = _env("API_KEY")
    if not base_url or not api_key:
        return False
    client = ApiClient(base_url=base_url, api_key=api_key)
    try:
        r = client.post("/internal/shutdown", data={})
        if r.status_code == 200:
            console.print("  [dim]API sinalizada para encerrar (POST /internal/shutdown).[/dim]")
            time.sleep(1.5)
            return True
    except Exception as e:
        logging.getLogger(__name__).debug("Shutdown API skip: %s", e)
    return False


# -----------------------------------------------------------------------------
# Storage cleanup
# -----------------------------------------------------------------------------


class StorageCleaner:
    """Limpeza de Redis (índices User/Product) e do arquivo SQLite."""

    def __init__(self, db_path: Path, console: Console) -> None:
        self._db_path = db_path
        self._console = console

    def clear_redis(
        self,
        user_service: User,
        product_service: Product,
    ) -> None:
        """Remove apenas os dados do Redis. Não altera o banco SQLite."""
        n_users = user_service.clear()
        n_products = product_service.clear()
        if n_users:
            self._console.print(f"  [dim]Limpos {n_users} usuários do Redis.[/dim]")
        if n_products:
            self._console.print(f"  [dim]Limpos {n_products} produtos do Redis.[/dim]")

    def delete_db(self) -> None:
        """Remove apenas o arquivo do banco SQLite."""
        if self._db_path.exists():
            self._db_path.unlink()
            self._console.print(f"  [dim]Banco SQLite removido: {self._db_path}[/dim]")


# -----------------------------------------------------------------------------
# Redis populate orchestration
# -----------------------------------------------------------------------------


class RedisPopulator:
    """Orquestra população de usuários e produtos no Redis e exibe amostras."""

    def __init__(
        self,
        user_service: User,
        product_service: Product,
        displayer: SampleDisplayer,
        user_count: int = POPULATE_USERS,
        product_count: int = POPULATE_PRODUCTS,
    ) -> None:
        self._user_service = user_service
        self._product_service = product_service
        self._displayer = displayer
        self._user_count = user_count
        self._product_count = product_count

    def run(self) -> None:
        """Popula usuários, exibe amostra e testes; depois produtos e amostra."""
        self._run_users()
        self._run_products()

    def _run_users(self) -> None:
        created = self._user_service.populate(self._user_count, id_prefix="fake", seed=42)
        self._displayer.show_user_populate(created, self._user_service.count())
        user_page = self._user_service.list_users(offset=0, limit=10, sort_by_age_asc=True)
        self._displayer.show_user_table(user_page)
        if user_page:
            self._displayer.show_user_uniqueness(user_page[0], self._user_service)

    def _run_products(self) -> None:
        created = self._product_service.populate(self._product_count, id_prefix="prod", seed=42)
        self._displayer.show_product_populate(created, self._product_service.count())
        product_page = self._product_service.list_products(
            offset=0, limit=10, sort_by_price_asc=True
        )
        self._displayer.show_product_table(product_page)
        if product_page:
            self._displayer.show_category_test(
                product_page[0].category,
                self._product_service,
            )


# -----------------------------------------------------------------------------
# Fallback test (API → Redis)
# -----------------------------------------------------------------------------


def _random_fallback_suffix() -> str:
    """Sufixo aleatório para IDs do teste de fallback (idempotência entre execuções)."""
    return secrets.token_hex(4)


def _random_cpf_11() -> str:
    """CPF aleatório de 11 dígitos (evita conflito de unicidade na API)."""
    return "".join(secrets.choice(digits) for _ in range(11))


class FallbackTester:
    """Testa fluxo cache miss → API (SQLite) → grava no Redis. Usa IDs/dados aleatórios por run (idempotente)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        user_service: User,
        product_service: Product,
        console: Console,
    ) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._user_service = user_service
        self._product_service = product_service
        self._console = console
        self._user_id = ""
        self._product_id = ""

    @classmethod
    def from_env(
        cls,
        user_service: User,
        product_service: Product,
        console: Console,
    ) -> "FallbackTester | None":
        """Constrói a partir de env; retorna None se API_BASE_URL ou API_KEY ausentes."""
        base_url = _env("API_BASE_URL")
        api_key = _env("API_KEY")
        if not base_url or not api_key:
            return None
        return cls(
            base_url=base_url,
            api_key=api_key,
            user_service=user_service,
            product_service=product_service,
            console=console,
        )

    def run(self) -> None:
        """Gera IDs únicos, seed na API, depois get com fallback_to_api e exibe resultado."""
        suffix = _random_fallback_suffix()
        self._user_id = f"fallback-user-{suffix}"
        self._product_id = f"fallback-prod-{suffix}"

        self._console.print()
        self._console.print(
            Panel.fit(
                "Teste fallback: cache miss → API (SQLite) → grava no Redis",
                title="Fallback API",
                border_style="magenta",
            )
        )
        self._console.print(f"  [dim]IDs desta execução: user={self._user_id!r} product={self._product_id!r}[/dim]")

        client = ApiClient(
            base_url=self._base_url,
            api_key=self._api_key,
        )
        self._seed_api(client)
        u, p = self._assert_fallback_get()
        self._assert_second_get_from_cache(u, p)

    def _seed_api(self, client: ApiClient) -> None:
        email = f"fallback-{_random_fallback_suffix()}@example.com"
        cpf = _random_cpf_11()
        r = client.post(
            "/users",
            data={
                "id": self._user_id,
                "name": "Fallback User",
                "email": email,
                "cpf": cpf,
                "age": 40,
                "weight": 70.0,
                "height": 1.75,
            },
        )
        if r.status_code not in {200, 201, 409}:
            self._console.print(f"  [red]POST /users: {r.status_code}[/red]")
        r = client.post(
            "/products",
            data={
                "id": self._product_id,
                "name": "Produto Fallback",
                "description": "Criado só na API",
                "category": "teste",
                "price": 99.90,
            },
        )
        if r.status_code not in {200, 201, 409}:
            self._console.print(f"  [red]POST /products: {r.status_code}[/red]")

    def _assert_fallback_get(self) -> tuple[Any, Any]:
        """Retorna (user_om | None, product_om | None)."""
        u = self._user_service.get(self._user_id, fallback_to_api=True)
        if u:
            self._console.print(
                f"  [green]User fallback (API → Redis):[/green] "
                f"id={u.id} name={u.name} email={u.email}"
            )
        else:
            self._console.print("  [red]User fallback: não encontrado (API está rodando?)[/red]")
        p = self._product_service.get(self._product_id, fallback_to_api=True)
        if p:
            self._console.print(
                f"  [green]Product fallback (API → Redis):[/green] "
                f"id={p.id} name={p.name} price={p.price}"
            )
        else:
            self._console.print("  [red]Product fallback: não encontrado (API está rodando?)[/red]")
        return (u, p)

    def _assert_second_get_from_cache(self, u: Any, p: Any) -> None:
        if not u or not p:
            return
        u2 = self._user_service.get(self._user_id, fallback_to_api=True)
        p2 = self._product_service.get(self._product_id, fallback_to_api=True)
        if u2 and p2:
            self._console.print("  [dim]Segundo get (from cache):[/dim] user ok, product ok")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

app = typer.Typer()
_console = Console()


@app.command()
def run_main(
    clean: bool = typer.Option(
        False,
        "--clean",
        help="Limpa Redis no início e remove banco SQLite ao final (após testes).",
    ),
) -> None:
    """Popula Redis com usuários e produtos; opcionalmente limpa storage com --clean."""
    user_service = User()
    product_service = Product()
    cleaner = StorageCleaner(_DEFAULT_DB_PATH, _console)
    displayer = SampleDisplayer(_console)
    populator = RedisPopulator(user_service, product_service, displayer)

    if clean:
        _console.print(
            Panel.fit(
                "Limpando apenas Redis (--clean); banco removido ao final.",
                border_style="yellow",
            )
        )
        cleaner.clear_redis(user_service, product_service)
        _console.print()

    populator.run()

    tester = FallbackTester.from_env(user_service, product_service, _console)
    if tester is None:
        _console.print()
        _console.print(
            "[dim]Teste de fallback omitido: defina API_BASE_URL e API_KEY no .env "
            "e deixe a API rodando (ex.: uv run run-api).[/dim]"
        )
    else:
        tester.run()

    if clean:
        _console.print()
        _console.print(
            Panel.fit(
                "Outras ações (--clean): shutdown da API e remoção do banco",
                border_style="yellow",
            )
        )
        _shutdown_api(_console)
        cleaner.delete_db()


def run() -> None:
    """Entry point para o comando run-main (pyproject.toml)."""
    app()


if __name__ == "__main__":
    app()
