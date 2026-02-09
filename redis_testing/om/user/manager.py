"""Managers ao estilo Django .objects: apenas acesso, não armazenados no Redis."""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .model import UserOM


class UserOMObjects:
    """Manager para UserOM."""

    model: type["UserOM"]

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
        """Cria e salva um UserOM.

        Args:
            user_id: Chave primária do usuário.
            name: Nome do usuário.
            email: Email do usuário.
            cpf: CPF do usuário.
            age: Idade do usuário.
            weight: Peso do usuário.
            height: Altura do usuário.

        Returns:
            UserOM: O usuário criado.

        """
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
        """Busca por id.

        Args:
            pk: Chave primária do usuário.

        Returns:
            UserOM: O usuário encontrado.

        """
        try:
            return self.model.get(pk)
        except Exception:
            return None

    def find_by_name(self, query: str, limit: int = 100) -> list["UserOM"]:
        """Busca por nome (full-text).

        Args:
            query: Query de busca.
            limit: Limite de resultados.

        Returns:
            Lista de usuários encontrados.

        """
        return list(self.model.find(self.model.name % query).copy(limit=limit).all())

    def find_by_email(self, email: str) -> list["UserOM"]:
        """Busca por email.

        Args:
            email: Email do usuário.

        Returns:
            Lista de usuários encontrados.

        """
        return list(self.model.find(self.model.email == email).all())

    def find_by_cpf(self, cpf: str) -> Optional["UserOM"]:
        """Busca por CPF.

        Args:
            cpf: CPF do usuário.

        Returns:
            Usuário encontrado ou None.

        """
        try:
            return self.model.find(self.model.cpf == cpf).first()
        except Exception:
            return None

    def list_all(
        self,
        offset: int = 0,
        limit: int = 10,
        *,
        sort_by_age_asc: bool = True,
    ) -> list["UserOM"]:
        """Lista os usuários, ordenado por idade.

        Args:
            offset: Offset.
            limit: Limite.
            sort_by_age_asc: Ordenar por idade ascendente.

        Returns:
            Lista de usuários encontrados.

        """
        q = self.model.find().sort_by("age" if sort_by_age_asc else "-age")
        return list(q.page(offset=offset, limit=limit))

    def count(self) -> int:
        """Conta o total de usuários.

        Returns:
            Total de usuários no índice.

        """
        return self.model.find().count()

    def delete(self, pk: str) -> bool:
        """Remove por id.

        Args:
            pk: Chave primária do usuário.

        Returns:
            True se o usuário foi removido, False caso contrário.

        """
        try:
            self.model.delete(pk)
            return True
        except Exception:
            return False
