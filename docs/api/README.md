# API FastAPI

API HTTP com SQLite, usada como fonte de verdade no fluxo de fallback. Mesmos schemas que o Redis (User, Product).

## Endpoints

### Users

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/users/{user_id}` | Retorna usuário por id (404 se não existir) |
| POST | `/users` | Cria usuário (409 se id já existe) |

### Products

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/products/search?q={query}&limit={n}` | Smart search (Redis) |
| GET | `/products/{product_id}` | Retorna produto por id (fallback) |
| POST | `/products` | Cria produto (409 se id já existe) |

## Autenticação

- **Header**: `Authorization: Bearer <API_KEY>`
- **Variável**: `API_KEY` no `.env`
- Não há suporte a `X-API-Key`

Exemplo:

```bash
curl -H "Authorization: Bearer sua-chave" \
  "http://localhost:8000/products/search?q=cerveja&limit=5"
```

## Schemas

- **UserCreate** / **UserResponse**: id, name, email, cpf, age, weight, height
- **ProductCreate** / **ProductResponse**: id, name, description, category, price
- **ProductSearchResponse**: meta (based_in, find_by, strategy), products

## Como rodar

```bash
uv run run-api
```

API em `http://localhost:8000`. Docs: `http://localhost:8000/docs`.
