# RedisCache Genérico

O `RedisCache[T]` é uma classe genérica que oferece cache unificado com suporte a:

- **JSON Storage**: armazena objetos complexos como JSON strings (ideal para modelos Pydantic)
- **Hash Storage**: armazena dados como hash Redis (eficiente para atualizações parciais)
- **Índices RediSearch**: permite busca reversa por campos indexados
- **TTL configurável**: expiração automática de chaves
- **Tratamento de erros**: decorator `handle_redis_error` que trata falhas Redis de forma silenciosa

## Exemplo de uso

```python
from redis_testing.cache import RedisCache
from redis_testing.utils import get_redis_client
from pydantic import BaseModel

class Produto(BaseModel):
    id: str
    nome: str
    preco: float

client = get_redis_client()

# Cache com JSON storage
cache = RedisCache[Produto](
    client=client,
    hash_prefix="produto:",
    ttl_seconds=3600,
    use_json_storage=True,
)

# Salvar
produto = Produto(id="1", nome="Notebook", preco=2999.90)
cache.save("prod-1", produto)

# Buscar
produto_recuperado = cache.get("prod-1", Produto)

# Busca reversa (requer índice)
cache = RedisCache[Produto](
    client=client,
    hash_prefix="produto_idx:",
    index_name="idx_produtos",
    indexed_fields=["categoria", "nome"],
    use_json_storage=False,
)
cache.ensure_index()
encontrado = cache.find_one("categoria", "eletrônicos", Produto)
```

## Arquitetura dos Exemplos

Os exemplos em `redis_testing/om/example.py`:

- **HashModelExample**: operações com HashModel (UserOM)
- **JsonModelExample**: operações com JsonModel (ProductOM)
- **CacheSimpleExample**: cache com strings, dicts
- **CacheModelExample**: cache com modelos Pydantic e índices RediSearch
- **ExampleRunner**: orquestra todos os exemplos

Execução: `uv run python main.py examples` | `uv run python main.py examples --clear`
