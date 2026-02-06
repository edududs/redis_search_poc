# redis_search_poc

POC para explorar **Redis Search** e **Redis OM**: indexação, buscas (full-text, por campo, ordenação) e cenário de cache com fallback para uma API HTTP.

## O que a POC cobre

- **Redis OM** (HashModel e JsonModel) para modelos tipados e CRUD no Redis.
- Uso de índices e buscas (find por email, CPF, categoria; full-text no nome; ordenação por idade/preço).
- **Cache com fallback**: em cache miss, busca na API (FastAPI + SQLite), persiste no Redis com TTL e retorna.
- API de fallback com os mesmos schemas (User, Product) para simular a “fonte de verdade”.

## Estrutura

- **`main.py`** — Script principal: popula Redis com usuários e produtos (faker), lista amostras, testes de busca e teste de fallback.
- **`redis_testing/`** — Modelos Redis OM (UserOM, ProductOM), managers e serviços com suporte a fallback para API.
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

## Comandos (pyproject.toml)

| Comando | Descrição |
|---------|-----------|
| `uv run run-main` | Roda o script principal (popula Redis, amostras, teste de fallback). |
| `uv run run-api` | Sobe a API FastAPI (porta 8000). |

## Fluxo de fallback

1. Cliente chama `user_service.get(id, fallback_to_api=True)` ou `product_service.get(id, fallback_to_api=True)`.
2. Se o dado está no Redis → retorna do cache.
3. Se não está (cache miss) → GET na API (`/users/{id}` ou `/products/{id}`), persiste no Redis com TTL e retorna.

A API (`api/`) é a “fonte de verdade” nesse cenário; o Redis atua como cache com expiração.
