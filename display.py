from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from redis_testing.om import Product, User, UserOM


class SampleDisplayer:
    """Renderização de painéis e tabelas para usuários e produtos."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def panel(self, title: str, content: str, border_style: str = "blue") -> None:
        self._console.print(Panel.fit(content, title=title, border_style=border_style))

    def show_user_populate(self, created: int, total: int) -> None:
        self._console.print(
            Panel.fit(
                "Populando usuários falsos",
                title="Redis OM — UserOM.objects",
                border_style="blue",
            )
        )
        self._console.print(f"  [green]Criados:[/green] {created} usuários")
        self._console.print(
            f"  [yellow]Total no índice (global):[/yellow] {total} "
            "[dim](acumula execuções anteriores)[/dim]"
        )

    def show_user_table(self, user_page: list) -> None:
        self._console.print()
        self._console.print(Panel.fit("Amostra usuários (primeiros 10)", border_style="blue"))
        table = Table(show_header=True, header_style="bold")
        table.add_column("id")
        table.add_column("name")
        table.add_column("email")
        table.add_column("age")
        for u in user_page:
            table.add_row(u.id, u.name, u.email, str(u.age))
        self._console.print(table)

    def show_user_uniqueness(
        self,
        first_user: "UserOM",
        user_service: "User",
    ) -> None:
        self._console.print()
        self._console.print(
            Panel.fit(
                "Teste unicidade usuário: get_by_email e get_by_cpf",
                border_style="blue",
            )
        )
        by_email = user_service.get_by_email(first_user.email)
        by_cpf = user_service.get_by_cpf(first_user.cpf)
        self._console.print(f"  get_by_email({first_user.email!r}): {len(by_email)} resultado(s)")
        self._console.print(
            f"  get_by_cpf({first_user.cpf!r}): {'1' if by_cpf else '0'} resultado(s)"
        )

    def show_product_populate(self, created: int, total: int) -> None:
        self._console.print()
        self._console.print(
            Panel.fit(
                "Populando produtos falsos",
                title="Redis OM — ProductOM.objects",
                border_style="green",
            )
        )
        self._console.print(f"  [green]Criados:[/green] {created} produtos")
        self._console.print(
            f"  [yellow]Total no índice (global):[/yellow] {total} "
            "[dim](acumula execuções anteriores)[/dim]"
        )

    def show_product_table(self, product_page: list) -> None:
        self._console.print()
        self._console.print(Panel.fit("Amostra produtos (primeiros 10)", border_style="green"))
        table = Table(show_header=True, header_style="bold")
        table.add_column("id")
        table.add_column("name")
        table.add_column("category")
        table.add_column("price")
        for p in product_page:
            table.add_row(p.id, p.name, p.category, f"R$ {p.price:.2f}")
        self._console.print(table)

    def show_category_test(
        self,
        category: str,
        product_service: "Product",
    ) -> None:
        self._console.print()
        self._console.print(Panel.fit(f"Teste get_by_category: {category!r}", border_style="green"))
        by_category = product_service.get_by_category(category)
        self._console.print(f"  get_by_category({category!r}): {len(by_category)} resultado(s)")
