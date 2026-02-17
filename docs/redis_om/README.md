# Redis OM

Modelos Redis OM (UserOM, ProductOM), RedisCache genérico e fluxo de fallback para API.

## Documentação

| Doc | Descrição |
|-----|-----------|
| [CACHE.md](CACHE.md) | RedisCache genérico (JSON/Hash, índices, busca reversa) |
| [FALLBACK.md](FALLBACK.md) | Fluxo cache miss → API → persist no Redis |

## Modelos

- **UserOM** (HashModel): usuários com busca por email, CPF, ordenação por idade
- **ProductOM** (JsonModel): produtos com busca full-text, por categoria, ordenação por preço

## Configuração Redis

`get_redis_client()` usa `host`, `port`, `db` por padrão (não lê REDIS_URL do env). Para usar URL:

```python
from redis_testing.utils import get_redis_client
import os
client = get_redis_client(url=os.getenv("REDIS_URL"))
```

Padrão: `host="localhost"`, `port=666`, `db=0`. Docker-compose expõe 666→6379.
