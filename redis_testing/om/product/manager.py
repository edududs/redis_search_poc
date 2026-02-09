"""Managers estilo Django .objects: não são campos, não vão pro Redis."""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .model import ProductOM


class ProductOMObjects:
    """Manager de ProductOM. Acesso via ProductOM.objects."""

    model: type["ProductOM"]

    def create(
        self,
        product_id: str,
        name: str,
        description: str,
        category: str,
        price: float = 0.0,
    ) -> "ProductOM":
        """Cria e salva um ProductOM.

        Args:
            product_id: Chave primária do produto.
            name: Nome do produto.
            description: Descrição do produto.
            category: Categoria do produto.
            price: Preço do produto.

        Returns:
            ProductOM: O produto criado.

        """
        inst = self.model(
            id=product_id,
            name=name,
            description=description,
            category=category,
            price=price,
        )
        inst.save()
        return inst

    def get(self, pk: str) -> Optional["ProductOM"]:
        """Busca por chave primária.

        Args:
            pk: Chave primária do produto.

        Returns:
            ProductOM: O produto encontrado.

        """
        try:
            return self.model.get(pk)
        except Exception:
            return None

    def find_by_name(self, query: str, limit: int = 100) -> list["ProductOM"]:
        """Busca por nome.

        Args:
            query: Query de busca.
            limit: Limite de resultados.

        Returns:
            Lista de produtos encontrados.

        """
        return list(self.model.find(self.model.name % query).copy(limit=limit).all())

    def find_by_category(self, category: str) -> list["ProductOM"]:
        """Busca por categoria.

        Args:
            category: Categoria do produto.

        Returns:
            Lista de produtos encontrados.

        """
        return list(self.model.find(self.model.category == category).all())

    def list_all(
        self,
        offset: int = 0,
        limit: int = 10,
        *,
        sort_by_price_asc: bool = True,
    ) -> list["ProductOM"]:
        """Lista todos os produtos.

        Args:
            offset: Offset.
            limit: Limite.
            sort_by_price_asc: Ordenar por preço ascendente.

        Returns:
            Lista de produtos encontrados.

        """
        q = self.model.find().sort_by("price" if sort_by_price_asc else "-price")
        return list(q.page(offset=offset, limit=limit))

    def count(self) -> int:
        """Conta o total de produtos.

        Returns:
            Total de produtos no índice.

        """
        return self.model.find().count()

    def delete(self, pk: str) -> bool:
        """Remove por chave primária.

        Args:
            pk: Chave primária do produto.

        Returns:
            True se o produto foi removido, False caso contrário.

        """
        try:
            self.model.delete(pk)
            return True
        except Exception:
            return False
