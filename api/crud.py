"""CRUD de usuários e produtos em SQLite (repositórios tipados)."""

from api.db import Database
from api.schemas import ProductCreate, ProductResponse, UserCreate, UserResponse


class UserRepository:
    """Repositório de usuários: get por id e insert."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, pk: str) -> UserResponse | None:
        """Obtém um usuário por id."""
        conn = self._db.get_connection()
        try:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (pk,)).fetchone()
            if row is None:
                return None
            d = self._db.row_to_dict(row)
            return UserResponse(
                id=d["id"],
                name=d["name"],
                email=d["email"],
                cpf=d["cpf"],
                age=d["age"],
                weight=d["weight"],
                height=d["height"],
            )
        finally:
            conn.close()

    def insert(self, data: UserCreate) -> UserResponse:
        """Insere um usuário."""
        conn = self._db.get_connection()
        try:
            conn.execute(
                "INSERT INTO users (id, name, email, cpf, age, weight, height) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    data.id,
                    data.name,
                    data.email,
                    data.cpf,
                    data.age,
                    data.weight,
                    data.height,
                ),
            )
            conn.commit()
            return UserResponse(
                id=data.id,
                name=data.name,
                email=data.email,
                cpf=data.cpf,
                age=data.age,
                weight=data.weight,
                height=data.height,
            )
        finally:
            conn.close()


class ProductRepository:
    """Repositório de produtos: get por id e insert."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, pk: str) -> ProductResponse | None:
        """Obtém um produto por id."""
        conn = self._db.get_connection()
        try:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (pk,)).fetchone()
            if row is None:
                return None
            d = self._db.row_to_dict(row)
            return ProductResponse(
                id=d["id"],
                name=d["name"],
                description=d["description"],
                category=d["category"],
                price=d["price"],
            )
        finally:
            conn.close()

    def insert(self, data: ProductCreate) -> ProductResponse:
        """Insere um produto."""
        conn = self._db.get_connection()
        try:
            conn.execute(
                "INSERT INTO products (id, name, description, category, price) VALUES (?, ?, ?, ?, ?)",
                (data.id, data.name, data.description, data.category, data.price),
            )
            conn.commit()
            return ProductResponse(
                id=data.id,
                name=data.name,
                description=data.description,
                category=data.category,
                price=data.price,
            )
        finally:
            conn.close()
