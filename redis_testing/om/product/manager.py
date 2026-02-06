"""Managers estilo Django .objects: não são campos, não vão pro Redis."""

from typing import TYPE_CHECKING, Optional, Type

if TYPE_CHECKING:
    from .model import ProductOM


class ProductOMObjects:
    """Manager de ProductOM. Acesso via ProductOM.objects."""

    model: Type["ProductOM"]

    def create(
        self,
        product_id: str,
        name: str,
        description: str,
        category: str,
        price: float = 0.0,
    ) -> "ProductOM":
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
        try:
            return self.model.get(pk)
        except Exception:
            return None

    def find_by_name(self, query: str, limit: int = 100) -> list["ProductOM"]:
        return list(self.model.find(self.model.name % query).copy(limit=limit).all())

    def find_by_category(self, category: str) -> list["ProductOM"]:
        return list(self.model.find(self.model.category == category).all())

    def list_all(
        self,
        offset: int = 0,
        limit: int = 10,
        sort_by_price_asc: bool = True,
    ) -> list["ProductOM"]:
        q = self.model.find().sort_by("price" if sort_by_price_asc else "-price")
        return list(q.page(offset=offset, limit=limit))

    def count(self) -> int:
        return self.model.find().count()

    def delete(self, pk: str) -> bool:
        try:
            self.model.delete(pk)
            return True
        except Exception:
            return False
