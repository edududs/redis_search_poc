"""Bootstrap: configura conexão e índices RediSearch. Chamar uma vez no startup."""

from typing import Any

from redis import Redis
from redis_om.model.migrations import SchemaDetector


def bootstrap(client: Redis) -> None:
    """Seta UserOM.Meta.database e ProductOM.Meta.database e cria/atualiza os índices."""
    from .product import ProductOM
    from .user import UserOM

    UserOM.Meta.database = client
    ProductOM.Meta.database = client
    SchemaDetector(conn=client).run()


class ManagerDescriptor:
    """Descriptor que vincula o manager à classe do modelo no primeiro acesso a .objects.

    Assim não é preciso fazer Model.objects.model = Model no final do arquivo:
    ao acessar UserOM.objects, criamos o manager, setamos model=UserOM e retornamos.
    """

    def __init__(self, manager_class: type) -> None:
        self.manager_class = manager_class
        self._cache: dict[type, Any] = {}

    def __get__(self, obj: Any, owner: type | None = None) -> Any:
        if owner is None:
            return self
        if owner not in self._cache:
            manager = self.manager_class()
            manager.model = owner  # type: ignore[attr-defined]
            self._cache[owner] = manager
        return self._cache[owner]
