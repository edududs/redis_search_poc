# Smart Search (Busca Inteligente)

Pipeline de busca com tolerância a typos, normalização de texto e aprendizado automático. Combina RediSearch, Redis Hash (dicionário) e Python para buscas de produtos que toleram variações de escrita (ex.: Heineken, Hinekken).

**Requer db=0** (RediSearch só suporta índices nesse database).

## Documentação

| Doc | Descrição |
|-----|-----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura técnica, componentes e fluxo |
| [USAGE.md](USAGE.md) | Guia de uso (código, API, exemplos) |
| [SHELL.md](SHELL.md) | Sequência de testes via shell (Python/IPython) |

## Uso rápido

```python
from redis_testing.om.product import product_service

products, meta = product_service.smart_search("cerveja Heineken", limit=10)
print(meta["strategy"], len(products))
```
