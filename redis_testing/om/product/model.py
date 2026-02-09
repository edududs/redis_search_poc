"""Modelo ProductOM (JsonModel). CRUD via ProductOM.objects."""

from typing import ClassVar

from redis import Redis
from redis_om import Field, JsonModel

from redis_testing.om.utils import ManagerDescriptor

from .manager import ProductOMObjects


class ProductOM(JsonModel, index=True):
    """Produto armazenado como documento JSON no Redis (JSON.SET/GET)."""

    objects: ClassVar[ProductOMObjects] = ManagerDescriptor(ProductOMObjects)

    id: str = Field(primary_key=True)
    name: str = Field(full_text_search=True)
    description: str = Field(full_text_search=True)
    category: str = Field(index=True)
    price: float = Field(sortable=True, default=0.0)

    class Meta:
        model_key_prefix = "product_om"
        global_key_prefix = "redis-om-testing"
        database: Redis | None = None
