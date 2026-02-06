import json
from logging import getLogger
from typing import Any, Callable

from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from redis_testing.om import Product, ProductOM, User, UserOM

_logger = getLogger(__name__)
_stderr_console = Console(stderr=True)


def print_redis_error(operation: str, prefix: str, error: Exception) -> None:
    """Exibe apenas a mensagem principal do erro Pydantic ou erro genérico."""
    if isinstance(error, ValidationError):
        # Extrai apenas o primeiro erro: "campo -> mensagem"
        err = error.errors()[0]
        loc = ".".join(map(str, err["loc"]))
        msg = f"[bold white]{loc}:[/bold white] {err['msg']}"
    else:
        msg = str(error)

    try:
        _stderr_console.print(
            Panel(
                msg,
                title=f"[red]Erro Redis: {operation} ({prefix})[/red]",
                border_style="red",
                expand=False,
            )
        )
    except Exception:
        _logger.warning(f"Redis op '{operation}' falhou ({prefix}): {msg}")


def format_value_for_display(value: Any) -> str:
    """Formata valor para exibição: dicts com mais de 2 chaves são indentados como JSON."""
    if isinstance(value, dict):
        if len(value) > 2:
            return json.dumps(value, indent=2, ensure_ascii=False)
        return str(value)
    return str(value)


def format_price(value: Any) -> str:
    """Formata valores numéricos como moeda brasileira."""
    if isinstance(value, (int, float)):
        return f"R$ {value:.2f}"
    return str(value)


def print_model_in_panel(
    console: Console, model: BaseModel, border_style: str = "blue"
) -> None:
    """Usa Rich.Pretty para formatar com syntax highlighting e exibir no Painel."""
    # Pretty do Rich aplica syntax highlighting automaticamente em modelos Pydantic
    pretty_content = Pretty(model, indent_guides=True, max_length=None)

    # Tenta pegar um título amigável
    title = getattr(model, "name", getattr(model, "nome", model.__class__.__name__))

    console.print()
    console.print(
        Panel(
            pretty_content,
            title=f"[{border_style}]{title}[/{border_style}]",
            border_style=border_style,
            expand=False,
        )
    )


class SampleDisplayer[T: BaseModel]:
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

    def _get_model_fields(self, model_type: type[BaseModel]) -> dict[str, Any]:
        """Extrai os campos do modelo Pydantic, filtrando campos internos."""
        if hasattr(model_type, "model_fields"):
            return {
                name: field_info
                for name, field_info in model_type.model_fields.items()
                if not name.startswith("_")
            }
        return {}

    def _show_model_table(
        self,
        model_type: type[T],
        instances: list[T],
        title: str,
        border_style: str = "blue",
        field_formatters: dict[str, Callable[[Any], str]] | None = None,
    ) -> None:
        """Renderiza uma tabela dinamicamente baseada nos campos do modelo Pydantic."""
        if not instances:
            return

        self._console.print()
        self._console.print(Panel.fit(title, border_style=border_style))

        model_fields = self._get_model_fields(model_type)
        if not model_fields:
            return

        table = Table(show_header=True, header_style="bold")
        formatters = field_formatters or {}

        for field_name in model_fields:
            table.add_column(field_name)

        for instance in instances:
            row_values = []
            for field_name in model_fields:
                value = getattr(instance, field_name, None)
                if field_name in formatters:
                    formatted_value = formatters[field_name](value)
                else:
                    formatted_value = str(value) if value is not None else ""
                row_values.append(formatted_value)
            table.add_row(*row_values)

        self._console.print(table)

    def show_user_table(self, user_page: list["UserOM"]) -> None:
        """Exibe tabela de usuários usando renderização dinâmica."""
        self._show_model_table(
            model_type=UserOM,
            instances=user_page,
            title="Amostra usuários (primeiros 10)",
            border_style="blue",
        )

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

        if len(by_email) == 1:
            print_model_in_panel(self._console, by_email[0], border_style="blue")
        else:
            self._console.print(
                f"  get_by_email({first_user.email!r}): {len(by_email)} resultado(s)"
            )

        if by_cpf:
            print_model_in_panel(self._console, by_cpf, border_style="blue")
        else:
            self._console.print(f"  get_by_cpf({first_user.cpf!r}): 0 resultado(s)")

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

    def show_product_table(self, product_page: list["ProductOM"]) -> None:
        """Exibe tabela de produtos usando renderização dinâmica com formatação customizada."""
        self._show_model_table(
            model_type=ProductOM,
            instances=product_page,
            title="Amostra produtos (primeiros 10)",
            border_style="green",
            field_formatters={"price": format_price},
        )

    def show_category_test(
        self,
        category: str,
        product_service: "Product",
    ) -> None:
        self._console.print()
        self._console.print(Panel.fit(f"Teste get_by_category: {category!r}", border_style="green"))
        by_category = product_service.get_by_category(category)

        if len(by_category) == 1:
            print_model_in_panel(self._console, by_category[0], border_style="green")
        else:
            self._console.print(f"  get_by_category({category!r}): {len(by_category)} resultado(s)")


class ExampleDisplayer:
    """Renderização centralizada para todos os exemplos do example.py."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def example_title_panel(self, title: str, subtitle: str, border_style: str = "blue") -> None:
        """Exibe painel de título de exemplo."""
        self.console.print(
            Panel.fit(subtitle, title=title, border_style=border_style)
        )

    def section_title(self, title: str) -> None:
        """Exibe título de seção."""
        self.console.print(f"\n[yellow]{title}[/yellow]")

    def creation_result(self, obj_id: str, obj_name: str, created: bool, price: float | None = None) -> None:
        """Exibe resultado de criação de objeto."""
        status = "Criado" if created else "Já existe"
        if price is not None:
            self.console.print(
                f"  [green]✓[/green] {status}: {obj_id} - {obj_name} (R$ {price:.2f})"
            )
        else:
            self.console.print(f"  [green]✓[/green] {status}: {obj_id} - {obj_name}")

    def get_result(self, key: str, result: BaseModel | None) -> None:
        """Exibe resultado de busca por chave primária."""
        if result:
            if hasattr(result, "name") and hasattr(result, "email"):
                self.console.print(f"  [cyan]get({key!r}):[/cyan] {result.name} ({result.email})")
            elif hasattr(result, "name") and hasattr(result, "category") and hasattr(result, "price"):
                self.console.print(
                    f"  [cyan]get({key!r}):[/cyan] {result.name} - {result.category} - R$ {result.price:.2f}"
                )
            else:
                self.console.print(f"  [cyan]get({key!r}):[/cyan] {result}")
        else:
            self.console.print("  [red]Objeto não encontrado[/red]")

    def find_result(
        self, operation: str, query: str, results: list[BaseModel] | BaseModel | None, border_style: str = "blue"
    ) -> None:
        """Exibe resultado de busca (find_by_*, search_by_*)."""
        if results is None:
            return

        if isinstance(results, BaseModel):
            print_model_in_panel(self.console, results, border_style=border_style)
        elif len(results) == 1:
            print_model_in_panel(self.console, results[0], border_style=border_style)
        elif len(results) > 1:
            name = results[0].name if hasattr(results[0], "name") else "resultado"
            query_str = f"({query!r})" if query else ""
            self.console.print(f"  [cyan]{operation}{query_str}:[/cyan] {name}")
        else:
            query_str = f"({query!r})" if query else ""
            self.console.print(f"  [cyan]{operation}{query_str}:[/cyan] 0 resultado(s)")

    def search_result(self, operation: str, query: str, count: int) -> None:
        """Exibe resultado de busca com contagem."""
        if count == 0:
            self.console.print(f"  [cyan]{operation}({query!r}):[/cyan] 0 resultado(s)")
        elif count == 1:
            self.console.print(f"  [cyan]{operation}({query!r}):[/cyan] 1 resultado(s)")
        else:
            self.console.print(f"  [cyan]{operation}({query!r}):[/cyan] {count} resultado(s)")

    def custom_table(
        self,
        title: str,
        columns: list[str],
        rows: list[list[str]],
        border_style: str = "blue",
    ) -> None:
        """Exibe tabela customizada."""
        self.console.print()
        self.console.print(Panel.fit(title, border_style=border_style))

        table = Table(show_header=True, header_style="bold")
        for col in columns:
            table.add_column(col)

        for row in rows:
            table.add_row(*row)

        self.console.print(table)

    def operation_result(self, operation: str, obj_id: str, details: str, success: bool | None = None) -> None:
        """Exibe resultado de operação (get_or_create, update_or_create, delete)."""
        if success is None:
            self.console.print(f"  [cyan]{operation}:[/cyan] {obj_id} {details}")
        elif success:
            self.console.print(f"  [cyan]{operation}:[/cyan] {obj_id} {details} [green]✓[/green]")
        else:
            self.console.print(f"  [cyan]{operation}:[/cyan] {obj_id} {details} [red]✗[/red]")

    def cache_get(self, key: str, value: Any) -> None:
        """Exibe resultado de cache.get()."""
        formatted = format_value_for_display(value)
        self.console.print(f"  [cyan]get({key!r}):[/cyan] {formatted}")

    def cache_exists(self, key: str, exists: bool) -> None:
        """Exibe resultado de cache.exists()."""
        self.console.print(f"  [cyan]exists({key!r}):[/cyan] {exists}")

    def cache_delete(self, key: str) -> None:
        """Exibe confirmação de cache.delete()."""
        self.console.print(f"  [cyan]delete({key!r})[/cyan] executado")

    def cache_find_one(self, field: str, value: str, result: BaseModel | None) -> None:
        """Exibe resultado de cache.find_one()."""
        if result:
            name = getattr(result, "nome", getattr(result, "name", "encontrado"))
            self.console.print(f"  [cyan]find_one({field!r}, {value!r}):[/cyan] {name}")
        else:
            self.console.print(f"  [cyan]find_one({field!r}, {value!r}):[/cyan] não encontrado")

    def cache_bulk_save(self, count: int, entity_name: str = "itens") -> None:
        """Exibe resultado de cache.bulk_save()."""
        self.console.print(f"  [cyan]bulk_save:[/cyan] {count} {entity_name} salvos")

    def success_panel(self, message: str) -> None:
        """Exibe painel de sucesso."""
        self.console.print()
        self.console.print(Panel.fit(message, border_style="green"))

    def cleanup_section(self) -> None:
        """Inicia seção de limpeza."""
        self.console.print()
        self.console.print(Panel.fit("Limpando dados dos exemplos", border_style="yellow"))

    def cleanup_result(self, count: int, entity_type: str) -> None:
        """Exibe resultado de limpeza."""
        self.console.print(f"  [dim]Limpos {count} {entity_type}[/dim]")

    def cleanup_index(self, index_name: str) -> None:
        """Exibe remoção de índice."""
        self.console.print(f"  [dim]Índice '{index_name}' removido[/dim]")

    def cleanup_complete(self) -> None:
        """Exibe conclusão de limpeza."""
        self.console.print("  [green]✓ Limpeza concluída[/green]")
