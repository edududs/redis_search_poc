# Smart Search — Sequência de Testes via Shell

Teste o fluxo de busca inteligente via Python interativo. Requer Redis (redis-stack) rodando. **db=0** obrigatório (RediSearch só suporta índices nesse database).

## Pré-requisitos

```bash
# 1. Subir Redis (redis-stack com RediSearch)
docker compose up -d

# 2. (Opcional) Instalar IPython para REPL mais rico
uv sync --extra shell
```

## Sequência de Comandos

### Opção A: Python interativo (`uv run python`)

```bash
uv run python
```

### Opção B: IPython (se instalado)

```bash
uv run ipython
```

### Comandos no REPL

```python
# --- 1. Imports ---
import time
from redis_testing.utils import get_redis_client
from redis_testing.om.utils import bootstrap
from redis_testing.om.product import Product, ProductOM, product_service
from redis_testing.name_normalization import normalize_name_for_search

# --- 2. Conectar ao Redis (porta 666 = docker-compose) ---
t0 = time.perf_counter()
client = get_redis_client(host="localhost", port=666, db=0)
bootstrap(client)
print(f"[conexão] {time.perf_counter() - t0:.3f}s")

# --- 3. Popular produtos de exemplo ---
t0 = time.perf_counter()
created = product_service.populate(20, id_prefix="p", seed=42)
print(f"[populate] {time.perf_counter() - t0:.3f}s  → {created} produtos")

# --- 4. Criar produto para testar busca (fake data não tem cerveja) ---
t0 = time.perf_counter()
product_service.create_product("p-heineken", "Cerveja Heineken 350ml", "Cerveja lager", "bebidas", 5.90)
print(f"[create_product] {time.perf_counter() - t0:.3f}s")

# --- 5. Busca direta (match exato) ---
t0 = time.perf_counter()
products, meta = product_service.smart_search("cerveja", limit=5)
print(f"[smart_search direct] {time.perf_counter() - t0:.3f}s")
print(f"  Estratégia: {meta['strategy']}, Encontrados: {len(products)}")
for p in products[:3]:
    print(f"  - {p.name} | {p.name_search}")

# --- 6. Busca com typo (fuzzy) ---
t0 = time.perf_counter()
products, meta = product_service.smart_search("cerveja Hinekken", limit=5)
print(f"[smart_search fuzzy] {time.perf_counter() - t0:.3f}s")
print(f"  Estratégia: {meta['strategy']}, Encontrados: {len(products)}")

# --- 7. Normalização (sem Redis, só Python) ---
print(normalize_name_for_search("Café de Leite 200 ml"))   # CAFE LEITE
print(normalize_name_for_search("Heineken 350ml"))         # HEINEKEN

# --- 8. Dicionário de aprendizado (Redis HSET/HGET) ---
from redis_testing.om.product.smart_search import SearchDictionaryManager
dict_mgr = SearchDictionaryManager(client)
t0 = time.perf_counter()
dict_mgr.set("skl", "SKOL")
print(f"[dict set] {time.perf_counter() - t0:.3f}s")
t0 = time.perf_counter()
r = dict_mgr.get("skl")
print(f"[dict get] {time.perf_counter() - t0:.3f}s  → {r}")
t0 = time.perf_counter()
r = dict_mgr.rewrite_query("CERVEJA SKL")
print(f"[dict rewrite_query] {time.perf_counter() - t0:.3f}s  → {r}")

# --- 9. Limpar e sair ---
t0 = time.perf_counter()
product_service.clear()
print(f"[clear] {time.perf_counter() - t0:.3f}s")
exit()
```

### Opção C: Teste via `python -c` (por etapas)

Útil para validar sem REPL. Execute cada bloco separadamente:

```bash
# Etapa 1: Imports e conexão
uv run python -c "
import time
from redis_testing.utils import get_redis_client
from redis_testing.om.utils import bootstrap
from redis_testing.om.product import product_service
from redis_testing.name_normalization import normalize_name_for_search
t0 = time.perf_counter()
client = get_redis_client(host='localhost', port=666, db=0)
bootstrap(client)
print('[conexão]', f'{time.perf_counter()-t0:.3f}s')
"

# Etapa 2: Popular e criar Heineken
uv run python -c "
import time
from redis_testing.utils import get_redis_client
from redis_testing.om.product import product_service
client = get_redis_client(host='localhost', port=666, db=0)
t0 = time.perf_counter()
created = product_service.populate(20, id_prefix='p', seed=42)
product_service.create_product('p-heineken', 'Cerveja Heineken 350ml', 'Cerveja lager', 'bebidas', 5.90)
print('[populate+create_product]', f'{time.perf_counter()-t0:.3f}s', '->', created + 1, 'produtos')
"

# Etapa 3: Busca
uv run python -c "
import time
from redis_testing.utils import get_redis_client
from redis_testing.om.product import product_service
from redis_testing.name_normalization import normalize_name_for_search
client = get_redis_client(host='localhost', port=666, db=0)
t0 = time.perf_counter()
products, meta = product_service.smart_search('cerveja', limit=5)
print('[smart_search direct]', f'{time.perf_counter()-t0:.3f}s')
print('  Estratégia:', meta['strategy'], 'Encontrados:', len(products))
for p in products[:3]:
    print('  -', p.name, '|', p.name_search)
print(normalize_name_for_search('Café de Leite 200 ml'))
print(normalize_name_for_search('Heineken 350ml'))
"
```

## Teste via API (curl)

```bash
# Subir API
uv run run-api &

# Busca (requer API_KEY no .env; API usa Authorization: Bearer)
curl -H "Authorization: Bearer sua-chave" "http://localhost:8000/products/search?q=cerveja&limit=5"
```

## Teste via pytest

```bash
uv run pytest redis_testing/om/product/tests/ -vv --cov=redis_testing.om.product --cov-report=term
```
