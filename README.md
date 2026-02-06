# redis_search_poc

POC para explorar **Redis Search** e **Redis OM**: indexação, buscas (full-text, por campo, ordenação) e cenário de cache com fallback para uma API HTTP.

## O que a POC cobre

- **Redis OM** (HashModel e JsonModel) para modelos tipados e CRUD no Redis.
- **RedisCache genérico**: cache unificado com suporte a JSON/Hash storage, índices RediSearch e busca reversa.
- Uso de índices e buscas (find por email, CPF, categoria; full-text no nome; ordenação por idade/preço).
- **Cache com fallback**: em cache miss, busca na API (FastAPI + SQLite), persiste no Redis com TTL e retorna.
- API de fallback com os mesmos schemas (User, Product) para simular a "fonte de verdade".
- **Exemplos completos**: demonstrações organizadas por classes de HashModel, JsonModel e RedisCache.

## Estrutura

- **`main.py`** — Script principal: popula Redis com usuários e produtos (faker), lista amostras, testes de busca e teste de fallback. Inclui comando `examples` para demonstrações completas.
- **`redis_testing/`** — Modelos Redis OM (UserOM, ProductOM), managers e serviços com suporte a fallback para API.
  - **`cache.py`** — `RedisCache[T]` genérico: cache unificado com suporte a Pydantic, JSON/Hash storage, índices RediSearch e busca reversa.
  - **`om/example.py`** — Exemplos completos organizados por classes: HashModel, JsonModel e RedisCache.
- **`api/`** — API FastAPI com SQLite: fonte de verdade para o cenário de fallback; mesmos schemas que o Redis.

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/) (ou Python 3.13+ com dependências instaladas)
- Redis (local ou via Docker, com suporte a Redis Search / Redis Stack)

## Variáveis de ambiente

Copie o exemplo e ajuste:

```bash
cp .env.example .env
```

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `API_BASE_URL` | URL da API de fallback | `http://localhost:8000` |
| `API_KEY` | Chave para `Authorization: Bearer` (API e cliente) | `your-secret-key` |
| `REDIS_URL` | URL do Redis | `redis://localhost:6379` ou `redis://localhost:666` (Docker) |
| `CLEAR_BEFORE_POPULATE` | Se `1`/`true`/`yes`, limpa índices antes de popular | (vazio ou `true`) |

O `.env` fica na raiz do projeto. Tanto o `main.py` quanto a API carregam esse arquivo.

## Como rodar

### 1. Redis

Com Docker (porta 666 no exemplo do `docker-compose`):

```bash
docker compose up -d
# REDIS_URL=redis://localhost:666
```

Ou use um Redis local na porta padrão (`REDIS_URL=redis://localhost:6379`).

### 2. API de fallback (para testar o fluxo de fallback)

Em um terminal:

```bash
uv sync
uv run run-api
```

A API sobe em `http://0.0.0.0:8000`. Documentação: `http://localhost:8000/docs`.

### 3. Script principal (popula Redis + teste de fallback)

Em outro terminal, com Redis (e opcionalmente a API) rodando:

```bash
uv run run-main
```

Ou:

```bash
uv run python main.py
```

- Popula Redis com usuários e produtos (faker).
- Lista amostras e testes de busca (email, CPF, categoria).
- Se `API_BASE_URL` e `API_KEY` estiverem definidos e a API estiver no ar, executa o **teste de fallback**: cria um user e um product só na API, faz `get` no Redis (cache miss), obtém da API, grava no Redis com TTL e mostra o segundo `get` vindo do cache.

### 4. Exemplos completos (HashModel, JsonModel e RedisCache)

Para ver demonstrações completas de todas as funcionalidades:

```bash
uv run python main.py examples
```

Com limpeza automática ao final (idempotente):

```bash
uv run python main.py examples --clear
```

Os exemplos demonstram:

- **HashModel (UserOM)**: CRUD completo, busca por campos, paginação e ordenação.
- **JsonModel (ProductOM)**: CRUD completo, busca full-text, busca por categoria.
- **RedisCache genérico**: cache de strings, dicts e modelos Pydantic com JSON/Hash storage e busca reversa via RediSearch.

## Comandos (pyproject.toml)

| Comando | Descrição |
|---------|-----------|
| `uv run run-main` | Roda o script principal (popula Redis, amostras, teste de fallback). |
| `uv run run-main --clean` | Limpa Redis antes e remove banco SQLite ao final. |
| `uv run python main.py examples` | Executa exemplos completos de HashModel, JsonModel e RedisCache. |
| `uv run python main.py examples --clear` | Executa exemplos e limpa todos os dados ao final (idempotente). |
| `uv run run-api` | Sobe a API FastAPI (porta 8000). |

## Fluxo de fallback

1. Cliente chama `user_service.get(id, fallback_to_api=True)` ou `product_service.get(id, fallback_to_api=True)`.
2. Se o dado está no Redis → retorna do cache.
3. Se não está (cache miss) → GET na API (`/users/{id}` ou `/products/{id}`), persiste no Redis com TTL e retorna.

A API (`api/`) é a "fonte de verdade" nesse cenário; o Redis atua como cache com expiração.

## RedisCache Genérico

O `RedisCache[T]` é uma classe genérica que oferece cache unificado com suporte a:

- **JSON Storage**: armazena objetos complexos como JSON strings (ideal para modelos Pydantic).
- **Hash Storage**: armazena dados como hash Redis (eficiente para atualizações parciais).
- **Índices RediSearch**: permite busca reversa por campos indexados.
- **TTL configurável**: expiração automática de chaves.
- **Tratamento de erros**: decorator que trata falhas Redis de forma silenciosa.

### Exemplo de uso

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

Os exemplos em `redis_testing/om/example.py` seguem uma arquitetura orientada a classes:

- **`HashModelExample`**: demonstra operações com HashModel (UserOM).
- **`JsonModelExample`**: demonstra operações com JsonModel (ProductOM).
- **`CacheSimpleExample`**: demonstra cache com valores simples (strings, dicts).
- **`CacheModelExample`**: demonstra cache com modelos Pydantic e índices RediSearch.
- **`ExampleRunner`**: orquestra a execução de todos os exemplos.

Todos os exemplos são **idempotentes**: podem ser executados múltiplas vezes sem problemas, especialmente com `--clear`.

## RedisCache Genérico

O `RedisCache[T]` é uma classe genérica que oferece cache unificado com suporte a:

- **JSON Storage**: armazena objetos complexos como JSON strings (ideal para modelos Pydantic).
- **Hash Storage**: armazena dados como hash Redis (eficiente para atualizações parciais).
- **Índices RediSearch**: permite busca reversa por campos indexados.
- **TTL configurável**: expiração automática de chaves.
- **Tratamento de erros**: decorator que trata falhas Redis de forma silenciosa.

### Exemplo de uso

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

Os exemplos em `redis_testing/om/example.py` seguem uma arquitetura orientada a classes:

- **`HashModelExample`**: demonstra operações com HashModel (UserOM).
- **`JsonModelExample`**: demonstra operações com JsonModel (ProductOM).
- **`CacheSimpleExample`**: demonstra cache com valores simples (strings, dicts).
- **`CacheModelExample`**: demonstra cache com modelos Pydantic e índices RediSearch.
- **`ExampleRunner`**: orquestra a execução de todos os exemplos.

Todos os exemplos são **idempotentes**: podem ser executados múltiplas vezes sem problemas, especialmente com `--clear`.
