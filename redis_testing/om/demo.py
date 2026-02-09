"""Funções de demo (um fluxo por função): HashModel e JsonModel com Rich."""

from redis import Redis
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .utils import bootstrap

console = Console()


def demo_user(client: Redis) -> None:
    """Demo HashModel (UserOM): bootstrap, criar, get, find, listar, contar, deletar."""
    from .user import user_service

    bootstrap(client)

    console.print(
        Panel.fit(
            "1. Criar usuários (UserOM.objects)",
            title="Demo Redis OM",
            border_style="blue",
        ),
    )

    u1 = user_service.create_user(
        user_id="demo-1",
        name="Alice Santos",
        email="alice@example.com",
        cpf="111.222.333-44",
        age=32,
        weight=58.5,
        height=1.62,
    )
    console.print("  [green]Criado:[/green]", u1)

    u2 = user_service.create_user(
        user_id="demo-2",
        name="Bob Silva",
        email="bob@example.com",
        cpf="555.666.777-88",
        age=28,
        weight=82.0,
        height=1.78,
    )
    console.print("  [green]Criado:[/green]", u2)

    console.print()
    console.print(
        Panel.fit("2. Get por chave primária (UserOM.objects.get)", border_style="blue"),
    )
    got = user_service.get_user("demo-1")
    console.print("  UserOM.objects.get('demo-1'):", got)

    console.print()
    console.print(Panel.fit("3. Find: nome, email e CPF", border_style="blue"))
    console.print(
        "  [cyan]find_by_name('Alice'):[/cyan]",
        user_service.find_by_name("Alice"),
    )
    console.print(
        "  [cyan]find_by_email('bob@...'):[/cyan]",
        user_service.find_by_email("bob@example.com"),
    )
    console.print(
        "  [cyan]find_by_cpf('555...'):[/cyan]",
        user_service.find_by_cpf("555.666.777-88"),
    )

    console.print()
    console.print(
        Panel.fit("4. Listar (paginação + ordenar por idade)", border_style="blue"),
    )
    page = user_service.list_users(offset=0, limit=5, sort_by_age_asc=True)
    table = Table(show_header=True, header_style="bold")
    table.add_column("id")
    table.add_column("name")
    table.add_column("age")
    for u in page:
        table.add_row(u.id, u.name, str(u.age))
    console.print(table)

    console.print()
    console.print("  [yellow]Total no índice:[/yellow]", user_service.count())

    console.print()
    console.print(Panel.fit("5. Deletar demo-2 e contar de novo", border_style="blue"))
    user_service.delete_user("demo-2")
    console.print("  [red]Deletado demo-2.[/red] Count agora:", user_service.count())


def demo_product(client: Redis) -> None:
    """Demo JsonModel (ProductOM): criar, get, find, listar, contar, deletar."""
    from .product import product_service

    bootstrap(client)

    console.print(
        Panel.fit(
            "1. Criar produtos (ProductOM.objects)",
            title="Demo JsonModel / ProductOM",
            border_style="green",
        ),
    )

    product_service.create_product(
        product_id="prod-1",
        name="Notebook Gamer",
        description="Notebook com GPU dedicada para jogos e trabalho",
        category="eletrônicos",
        price=5499.90,
    )
    console.print("  [green]Criado prod-1[/green]")

    product_service.create_product(
        product_id="prod-2",
        name="Teclado Mecânico",
        description="Teclado mecânico RGB switches azuis",
        category="periféricos",
        price=399.90,
    )
    console.print("  [green]Criado prod-2[/green]")

    product_service.create_product(
        product_id="prod-3",
        name="Mouse Gamer",
        description="Mouse gamer 16000 DPI",
        category="periféricos",
        price=249.90,
    )
    console.print("  [green]Criado prod-3[/green]")

    console.print()
    console.print(
        Panel.fit(
            "2. Get por chave primária (ProductOM.objects.get)",
            border_style="green",
        ),
    )
    got = product_service.get_product("prod-1")
    console.print("  ProductOM.objects.get('prod-1'):", got)

    console.print()
    console.print(
        Panel.fit("3. Find: nome (full-text) e categoria (exato)", border_style="green"),
    )
    console.print(
        "  [cyan]find_product_by_name('Gamer'):[/cyan]",
        product_service.find_by_name("Gamer"),
    )
    console.print(
        "  [cyan]find_product_by_category('periféricos'):[/cyan]",
        product_service.find_by_category("periféricos"),
    )

    console.print()
    console.print(
        Panel.fit("4. Listar (paginação + ordenar por preço)", border_style="green"),
    )
    page = product_service.list_products(offset=0, limit=5, sort_by_price_asc=True)
    table = Table(show_header=True, header_style="bold")
    table.add_column("id")
    table.add_column("name")
    table.add_column("category")
    table.add_column("price")
    for p in page:
        table.add_row(p.id, p.name, p.category, f"R$ {p.price:.2f}")
    console.print(table)

    console.print()
    console.print(
        "  [yellow]Total de produtos no índice:[/yellow]",
        product_service.count(),
    )

    console.print()
    console.print(Panel.fit("5. Deletar prod-3 e contar de novo", border_style="green"))
    product_service.delete_product("prod-3")
    console.print("  [red]Deletado prod-3.[/red] Count agora:", product_service.count())
