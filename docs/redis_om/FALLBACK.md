# Fluxo de Fallback (Cache Miss)

Quando o Redis não encontra o dado, o serviço busca na API (fonte de verdade) e persiste no Redis com TTL.

## Sequência

1. Cliente chama `user_service.get(id, fallback_to_api=True)` ou `product_service.get(id, fallback_to_api=True)`
2. Redis: busca por chave primária
3. Se encontrado → retorna do cache
4. Se não (cache miss) → GET na API (`/users/{id}` ou `/products/{id}`)
5. Persiste no Redis com TTL (opcional via `ttl_seconds`)
6. Retorna o dado

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `API_BASE_URL` | URL da API (ex.: `http://localhost:8000`) |
| `API_KEY` | Chave para `Authorization: Bearer` |

## Configuração do serviço

```python
from redis_testing.om.product import Product

# Com fallback habilitado por padrão
product_service = Product(fallback_to_api=True)

# Ou em uma instância específica
product_service.fallback_to_api = True
```

## API como fonte de verdade

A API (`api/`) usa SQLite e expõe os mesmos schemas (User, Product). O Redis atua como cache com expiração.
