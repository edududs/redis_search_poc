from pydantic import BaseModel
from redis import Redis
from redis.commands.search.field import TagField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType

from .utils import get_redis_client

INDEX_NAME = "user-idx"


class User(BaseModel):
    id: str
    name: str
    email: str
    cpf: str
    age: int
    weight: float
    height: float


def setup_index(client: Redis, index_name: str) -> None:
    """Create RediSearch index for user hashes with prefix user:."""
    try:
        client.ft(index_name).info()
    except Exception:
        schema = (
            TextField("name"),
            TagField("email"),
            TagField("cpf"),
            TagField("id"),
        )
        definition = IndexDefinition(
            prefix=["user:"],
            index_type=IndexType.HASH,
        )
        client.ft(index_name).create_index(schema, definition=definition)


def create_user(client: Redis, user: User) -> User:
    user_key = f"user:{user.id}"
    client.hset(user_key, mapping=user.model_dump())
    return user


def get_user(client: Redis, user_id: str):
    user_key = f"user:{user_id}"
    user = client.hgetall(user_key)
    return User(**user)


def main():
    client = get_redis_client()
    setup_index(client=client, index_name=INDEX_NAME)
    user = User(
        id="1",
        name="John Doe",
        email="john.doe@example.com",
        cpf="123.456.789-00",
        age=30,
        weight=75.5,
        height=1.78,
    )
    create_user(client=client, user=user)
    print("Get sem o Redis OM:", get_user(client=client, user_id="1"))
