"""Modelo UserOM (HashModel). CRUD via UserOM.objects."""

from typing import ClassVar, Optional

from redis import Redis
from redis_om import Field, HashModel

from ..utils import ManagerDescriptor
from .manager import UserOMObjects


class UserOM(HashModel, index=True):
    """Usuário armazenado como hash no Redis; campos indexados permitem find() e ordenação."""

    objects: ClassVar[UserOMObjects] = ManagerDescriptor(UserOMObjects)

    id: str = Field(primary_key=True)
    name: str = Field(full_text_search=True)
    email: str = Field(index=True)
    cpf: str = Field(index=True)
    age: int = Field(default=0, sortable=True)
    weight: float = 0.0
    height: float = 0.0

    class Meta:
        model_key_prefix = "user-om-testing"
        global_key_prefix = "redis-om-testing"
        database: Optional[Redis] = None
