import re
from pathlib import Path

from dotenv import load_dotenv
from dotenv.main import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from redis_testing.om import Product, User
from redis_testing.utils import ApiClient

_PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(_PROJECT_ROOT / ".env")
API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CLEAR_BEFORE_POPULATE = bool(
    re.fullmatch(
        r"(1|true|yes|sim|on|y|s)", os.getenv("CLEAR_BEFORE_POPULATE", "").strip(), re.IGNORECASE
    )
)
console = Console()

POPULATE_USERS = 300
POPULATE_PRODUCTS = 300


def main() -> None:
    product_service, user_service = Product(), User()

    # --- Etapa: usuários ---
    if CLEAR_BEFORE_POPULATE:
        n = user_service.clear()
        if n:
            console.print(f"  [dim]Limpos {n} usuários do índice (CLEAR_BEFORE_POPULATE).[/dim]")
    console.print(
        Panel.fit(
            "Populando usuários falsos",
            title="Redis OM — UserOM.objects",
            border_style="blue",
        )
    )
    created_u = user_service.populate(POPULATE_USERS, id_prefix="fake", seed=42)
    console.print(f"  [green]Criados:[/green] {created_u} usuários")
    console.print(
        f"  [yellow]Total no índice (global):[/yellow] {user_service.count()} "
        "[dim](acumula execuções anteriores)[/dim]"
    )

    console.print()
    console.print(Panel.fit("Amostra usuários (primeiros 10)", border_style="blue"))
    user_page = user_service.list_users(offset=0, limit=10, sort_by_age_asc=True)
    user_table = Table(show_header=True, header_style="bold")
    user_table.add_column("id")
    user_table.add_column("name")
    user_table.add_column("email")
    user_table.add_column("age")
    for u in user_page:
        user_table.add_row(u.id, u.name, u.email, str(u.age))
    console.print(user_table)

    if user_page:
        first_user = user_page[0]
        console.print()
        console.print(
            Panel.fit(
                "Teste unicidade usuário: get_by_email e get_by_cpf",
                border_style="blue",
            )
        )
        by_email = user_service.get_by_email(first_user.email)
        by_cpf = user_service.get_by_cpf(first_user.cpf)
        console.print(f"  get_by_email({first_user.email!r}): {len(by_email)} resultado(s)")
        console.print(f"  get_by_cpf({first_user.cpf!r}): {'1' if by_cpf else '0'} resultado(s)")

    # --- Etapa: produtos ---
    if CLEAR_BEFORE_POPULATE:
        n = product_service.clear()
        if n:
            console.print(f"  [dim]Limpos {n} produtos do índice (CLEAR_BEFORE_POPULATE).[/dim]")
    console.print()
    console.print(
        Panel.fit(
            "Populando produtos falsos",
            title="Redis OM — ProductOM.objects",
            border_style="green",
        )
    )
    created_p = product_service.populate(POPULATE_PRODUCTS, id_prefix="prod", seed=42)
    console.print(f"  [green]Criados:[/green] {created_p} produtos")
    console.print(
        f"  [yellow]Total no índice (global):[/yellow] {product_service.count()} "
        "[dim](acumula execuções anteriores)[/dim]"
    )

    console.print()
    console.print(Panel.fit("Amostra produtos (primeiros 10)", border_style="green"))
    product_page = product_service.list_products(offset=0, limit=10, sort_by_price_asc=True)
    product_table = Table(show_header=True, header_style="bold")
    product_table.add_column("id")
    product_table.add_column("name")
    product_table.add_column("category")
    product_table.add_column("price")
    for p in product_page:
        product_table.add_row(p.id, p.name, p.category, f"R$ {p.price:.2f}")
    console.print(product_table)

    if product_page:
        cat = product_page[0].category
        console.print()
        console.print(Panel.fit(f"Teste get_by_category: {cat!r}", border_style="green"))
        by_category = product_service.get_by_category(cat)
        console.print(f"  get_by_category({cat!r}): {len(by_category)} resultado(s)")

    _run_fallback_test(user_service, product_service)


def _run_fallback_test(user_service: User, product_service: Product) -> None:
    """Testa fallback: dados só na API (SQLite), get no Redis com fallback_to_api=True."""
    if not API_BASE_URL or not API_KEY:
        console.print()
        console.print(
            "[dim]Teste de fallback omitido: defina API_BASE_URL e API_KEY no .env "
            "e deixe a API rodando (ex.: uv run run-api).[/dim]"
        )
        return

    console.print()
    console.print(
        Panel.fit(
            "Teste fallback: cache miss → API (SQLite) → grava no Redis",
            title="Fallback API",
            border_style="magenta",
        )
    )

    client = ApiClient(base_url=API_BASE_URL, api_key=API_KEY)

    def _seed_api() -> None:
        r = client.post(
            "/users",
            data={
                "id": "fallback-user-1",
                "name": "Fallback User",
                "email": "fallback@example.com",
                "cpf": "999.888.777-66",
                "age": 40,
                "weight": 70.0,
                "height": 1.75,
            },
        )
        if r.status_code not in {200, 201, 409}:
            console.print(f"  [red]POST /users: {r.status_code}[/red]")
        r = client.post(
            "/products",
            data={
                "id": "fallback-prod-1",
                "name": "Produto Fallback",
                "description": "Criado só na API",
                "category": "teste",
                "price": 99.90,
            },
        )
        if r.status_code not in {200, 201, 409}:
            console.print(f"  [red]POST /products: {r.status_code}[/red]")

    _seed_api()

    u = user_service.get("fallback-user-1", fallback_to_api=True)
    if u:
        console.print(
            f"  [green]User fallback (API → Redis):[/green] id={u.id} name={u.name} email={u.email}"
        )
    else:
        console.print("  [red]User fallback: não encontrado (API está rodando?)[/red]")

    p = product_service.get("fallback-prod-1", fallback_to_api=True)
    if p:
        console.print(
            f"  [green]Product fallback (API → Redis):[/green] id={p.id} name={p.name} price={p.price}"
        )
    else:
        console.print("  [red]Product fallback: não encontrado (API está rodando?)[/red]")

    if u and p:
        u2 = user_service.get("fallback-user-1", fallback_to_api=True)
        p2 = product_service.get("fallback-prod-1", fallback_to_api=True)
        console.print(
            "  [dim]Segundo get (from cache):[/dim] user ok, product ok" if u2 and p2 else ""
        )


def run() -> None:
    """Entry point para o comando run-main (pyproject.toml)."""
    main()


if __name__ == "__main__":
    main()
