"""Exemplo de uso do RedisCache genérico."""

from pydantic import BaseModel

from redis_testing.cache import RedisCache
from redis_testing.utils import get_redis_client


# Exemplo 1: Cache simples com valores primitivos
def exemplo_cache_simples():
    """Cache de strings simples."""
    client = get_redis_client()

    cache = RedisCache[str](
        client=client,
        hash_prefix="simple:",
        ttl_seconds=300,
    )

    # Salvar
    cache.save("chave1", "valor1")
    cache.save("chave2", "valor2")

    # Buscar
    valor = cache.get("chave1")
    print(f"Valor recuperado: {valor}")

    # Verificar existência
    existe = cache.exists("chave1")
    print(f"Chave existe: {existe}")

    # Deletar
    cache.delete("chave1")


# Exemplo 2: Cache com modelos Pydantic
class Produto(BaseModel):
    """Modelo de exemplo."""

    id: str
    nome: str
    preco: float
    categoria: str


def exemplo_cache_com_modelo():
    """Cache com modelos Pydantic."""
    client = get_redis_client()

    # Usando JSON storage (mais eficiente para objetos complexos)
    cache = RedisCache[Produto](
        client=client,
        hash_prefix="produto:",
        ttl_seconds=3600,
        use_json_storage=True,  # Armazena como JSON string
    )

    produto = Produto(
        id="prod-1",
        nome="Notebook",
        preco=2999.90,
        categoria="eletrônicos",
    )

    # Salvar
    cache.save("prod-1", produto)

    # Buscar com tipo
    produto_recuperado = cache.get("prod-1", Produto)
    print(f"Produto recuperado: {produto_recuperado}")

    # Buscar sem tipo (retorna dict)
    produto_dict = cache.get("prod-1")
    print(f"Produto como dict: {produto_dict}")


# Exemplo 3: Cache com Hash storage e índices RediSearch
def exemplo_cache_com_indice():
    """Cache com Hash storage e busca reversa via RediSearch."""
    client = get_redis_client()

    cache = RedisCache[Produto](
        client=client,
        hash_prefix="produto_idx:",
        index_name="idx_produtos",
        indexed_fields=["categoria", "nome"],  # Campos indexados para busca
        ttl_seconds=3600,
        use_json_storage=False,  # Usa Hash storage
    )

    # Garantir que o índice existe
    cache.ensure_index()

    produto1 = Produto(
        id="prod-1",
        nome="Notebook Gamer",
        preco=4999.90,
        categoria="eletrônicos",
    )

    produto2 = Produto(
        id="prod-2",
        nome="Teclado Mecânico",
        preco=399.90,
        categoria="periféricos",
    )

    # Salvar produtos
    cache.save("prod-1", produto1)
    cache.save("prod-2", produto2)

    # Busca reversa por categoria
    produto_encontrado = cache.find_one("categoria", "eletrônicos", Produto)
    print(f"Produto encontrado por categoria: {produto_encontrado}")

    # Bulk save
    produtos_bulk = [
        ("prod-3", Produto(id="prod-3", nome="Mouse", preco=199.90, categoria="periféricos")),
        ("prod-4", Produto(id="prod-4", nome="Monitor", preco=1299.90, categoria="eletrônicos")),
    ]
    salvos = cache.bulk_save(produtos_bulk)
    print(f"Produtos salvos em bulk: {salvos}")


# Exemplo 4: Cache com dict simples
def exemplo_cache_com_dict():
    """Cache com dicionários Python."""
    client = get_redis_client()

    cache = RedisCache[dict](
        client=client,
        hash_prefix="dict:",
        ttl_seconds=600,
    )

    dados = {
        "usuario": "alice",
        "email": "alice@example.com",
        "idade": 30,
    }

    cache.save("user-1", dados)

    dados_recuperados = cache.get("user-1")
    print(f"Dados recuperados: {dados_recuperados}")


if __name__ == "__main__":
    print("=== Exemplo 1: Cache Simples ===")
    exemplo_cache_simples()

    print("\n=== Exemplo 2: Cache com Modelo Pydantic ===")
    exemplo_cache_com_modelo()

    print("\n=== Exemplo 3: Cache com Índice RediSearch ===")
    exemplo_cache_com_indice()

    print("\n=== Exemplo 4: Cache com Dict ===")
    exemplo_cache_com_dict()
