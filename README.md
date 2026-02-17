# Redis Search Lab

> POC para explorar **Redis Search** e **Redis OM**: indexação, buscas full-text, cache com fallback para API e busca inteligente com tolerância a typos.

---

## Início rápido

```bash
docker compose up -d          # Redis
uv run run-main              # Popula e testa
```

Documentação detalhada: [docs/](docs/)

---

## O que este projeto oferece

| Área | Funcionalidades |
|------|-----------------|
| **Redis OM** | HashModel (UserOM), JsonModel (ProductOM), CRUD, buscas por campo, full-text, ordenação |
| **Smart Search** | Pipeline com tolerância a typos: direct → dictionary → fuzzy → spellcheck → learn |
| **Normalização** | `normalize_name_for_search` — acentos, stopwords, unidades (200ml, 1L) |
| **RedisCache** | JSON/Hash storage, índices RediSearch, busca reversa, TTL |
| **Fallback** | Cache miss → API (SQLite) → persist no Redis |
| **API** | FastAPI com endpoints users/products, auth Bearer, search, CRUD |
| **CLI** | `main.py` — populate, examples, teste de fallback |
| **Testes** | pytest, fixtures, cobertura (smart search, normalização, integração) |

---

## Tecnologias

`Redis Stack` · `Redis OM` · `FastAPI` · `SQLite` · `Pydantic` · `Typer` · `Faker` · `Rich` · `uv`

---

## Comandos

| Comando | Descrição |
|---------|-----------|
| `uv run run-main` | Popula Redis, amostras, teste de fallback |
| `uv run run-main --clean` | Limpa Redis e remove SQLite ao final |
| `uv run python main.py examples` | Exemplos HashModel, JsonModel, RedisCache |
| `uv run python main.py examples --clear` | Exemplos + limpeza ao final |
| `uv run run-api` | Sobe API FastAPI (porta 8000) |
| `uv run pytest redis_testing/om/product/tests/` | Testes do Smart Search |

---

## Configuração

**Pré-requisitos:** [uv](https://docs.astral.sh/uv/) (ou Python 3.13+) · Redis Stack (`docker compose up -d`)

```bash
cp .env.example .env
```

| Variável | Descrição |
|----------|-----------|
| `API_BASE_URL` | URL da API de fallback |
| `API_KEY` | Chave para `Authorization: Bearer` |
| `REDIS_URL` | URL do Redis (opcional) |
| `CLEAR_BEFORE_POPULATE` | `1`/`true`/`yes` para limpar índices antes de popular |

---

## Como rodar

```bash
# 1. Redis
docker compose up -d

# 2. API (opcional, para fallback)
uv run run-api

# 3. Script principal
uv run run-main
```

---

## Documentação

| Escopo | Descrição |
|--------|-----------|
| [**Smart Search**](docs/smart_search/) | Busca inteligente (typos, normalização, aprendizado) |
| [**Redis OM**](docs/redis_om/) | Modelos, cache, fallback |
| [**API**](docs/api/) | Endpoints, autenticação, schemas |
| [**Testes**](docs/tests/) | Fixtures, estrutura, comandos |

---

## Estrutura do projeto

```
main.py              # CLI: populate, examples, teste de fallback
redis_testing/       # UserOM, ProductOM, RedisCache, Smart Search
api/                 # FastAPI + SQLite (fonte de verdade para fallback)
docs/                # Documentação por escopo
```
