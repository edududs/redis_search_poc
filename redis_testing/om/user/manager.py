"""Managers ao estilo Django .objects: apenas acesso, não armazenados no Redis."""

from typing import TYPE_CHECKING, List, Optional, Type

if TYPE_CHECKING:
    from .model import UserOM


class UserOMObjects:
    """Manager para UserOM."""

    model: Type["UserOM"]

    def create(
        self,
        user_id: str,
        name: str,
        email: str,
        cpf: str,
        age: int = 0,
        weight: float = 0.0,
        height: float = 0.0,
    ) -> "UserOM":
        """Cria e salva um UserOM."""
        inst = self.model(
            id=user_id,
            name=name,
            email=email,
            cpf=cpf,
            age=age,
            weight=weight,
            height=height,
        )
        inst.save()
        return inst

    def get(self, pk: str) -> Optional["UserOM"]:
        """Busca por id."""
        try:
            return self.model.get(pk)
        except Exception:
            return None

    def find_by_name(self, query: str, limit: int = 100) -> List["UserOM"]:
        """Busca por nome (full-text)."""
        return list(self.model.find(self.model.name % query).copy(limit=limit).all())

    def find_by_email(self, email: str) -> List["UserOM"]:
        """Busca por email."""
        return list(self.model.find(self.model.email == email).all())

    def find_by_cpf(self, cpf: str) -> Optional["UserOM"]:
        """Busca por CPF."""
        try:
            return self.model.find(self.model.cpf == cpf).first()
        except Exception:
            return None

    def list_all(
        self,
        offset: int = 0,
        limit: int = 10,
        sort_by_age_asc: bool = True,
    ) -> List["UserOM"]:
        """Lista os usuários, ordenado por idade."""
        q = self.model.find().sort_by("age" if sort_by_age_asc else "-age")
        return list(q.page(offset=offset, limit=limit))

    def count(self) -> int:
        """Conta o total de usuários."""
        return self.model.find().count()

    def delete(self, pk: str) -> bool:
        """Remove por id."""
        try:
            self.model.delete(pk)
            return True
        except Exception:
            return False
