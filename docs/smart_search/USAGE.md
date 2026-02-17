# Smart Search — Guia de Uso

Como utilizar a busca inteligente em código, API e testes.

## 1. Via Serviço Python

```python
from redis_testing.om.product import product_service

products, metadata = product_service.smart_search("cerveja Heineken", limit=10)

print(metadata)
# {"based_in": "cerveja Heineken", "find_by": "CERVEJA HEINEKEN", "strategy": "direct"}

for p in products:
    print(p.name, p.name_search, p.price)
```

### Estratégias de retorno

| strategy    | Significado                                      |
|------------|---------------------------------------------------|
| `direct`   | Match exato ou fonético (PHONETIC dm:pt) no `name_search` |
| `dictionary` | Query reescrita pelo dicionário aprendido     |
| `fuzzy`   | Match aproximado (Levenshtein)                    |
| `spellcheck` | Sugestão do RediSearch FT.SPELLCHECK           |
| `empty`    | Query vazia ou só stopwords                       |
| `not_found` | Nenhuma estratégia encontrou resultados        |

## 2. Via API REST

```bash
# Busca simples (API usa Authorization: Bearer)
curl -H "Authorization: Bearer SUA_CHAVE" \
  "http://localhost:8000/products/search?q=cerveja&limit=5"

# Resposta
{
  "meta": {"based_in": "cerveja", "find_by": "CERVEJA", "strategy": "direct"},
  "products": [...]
}
```

## 3. Normalização manual

```python
from redis_testing.name_normalization import normalize_name_for_search

normalize_name_for_search("Café Pilão 500g")   # "CAFE PILAO"
normalize_name_for_search("Heineken 350ml")    # "HEINEKEN"
normalize_name_for_search("de da do")          # ""
```

## 4. Dicionário de aprendizado

```python
from redis_testing.utils import get_redis_client
from redis_testing.om.product.smart_search import SearchDictionaryManager

client = get_redis_client()
dict_mgr = SearchDictionaryManager(client)

# Gravar mapeamento (typo → correto)
dict_mgr.set("Hinekken", "HEINEKEN")
dict_mgr.set("skl", "SKOL")

# Consultar
dict_mgr.get("Hinekken")  # "HEINEKEN"

# Reescrever query
dict_mgr.rewrite_query("CERVEJA HINEKKEN")  # "CERVEJA HEINEKEN"
```

## 5. Criar produtos com name_search

```python
from redis_testing.om.product import product_service

# Via serviço (recomendado; faz bootstrap automaticamente)
product = product_service.create_product(
    product_id="p-1",
    name="Cerveja Heineken 350ml",
    description="Cerveja importada",
    category="bebidas",
    price=8.50,
)
# name_search é normalizado automaticamente

# Ou via manager (requer bootstrap prévio)
from redis_testing.om.product import ProductOM
from redis_testing.om.utils import bootstrap
from redis_testing.utils import get_redis_client
client = get_redis_client(host="localhost", port=666, db=0)
bootstrap(client)
product = ProductOM.objects.create(
    product_id="p-1",
    name="Cerveja Heineken 350ml",
    description="Cerveja importada",
    category="bebidas",
    name_search="CERVEJA HEINEKEN",  # opcional; normaliza se omitido
    price=8.50,
)
```

## 6. Popular e limpar

```python
from redis_testing.om.product import product_service

# Criar N produtos fake (retorna int)
created = product_service.populate(50, id_prefix="prod", seed=42)

# Limpar todos (retorna quantidade removida)
n = product_service.clear()
```

## 7. Configuração

| Variável / Parâmetro | Padrão   | Descrição                    |
|----------------------|----------|------------------------------|
| `host`               | localhost| Host do Redis                |
| `port`               | 666      | Porta (docker-compose)       |
| `db`                 | 0        | Database (apenas 0 para índices) |
| `limit`              | 100      | Limite de resultados na busca |

`get_redis_client()` aceita `url` opcional; se não passado, usa `host`/`port`/`db`. O código atual não lê `REDIS_URL` do env automaticamente.

## 8. Exemplos de queries

| Query           | Comportamento esperado                          |
|-----------------|--------------------------------------------------|
| `cerveja`       | Produtos com CERVEJA no name_search             |
| `cerveja Hinekken` | Fuzzy encontra HEINEKEN; aprende mapeamento  |
| `café pilão`    | Normaliza para CAFE PILAO; match direto          |
| `Heineken`      | Match direto (case-insensitive após normalizar)  |
| `de da do`      | Retorna vazio (strategy: empty)                 |
