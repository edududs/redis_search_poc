# Testes

Estrutura de testes, fixtures e comandos.

## Smart Search (redis_testing/om/product/tests/)

Testes abrangentes para o sistema de busca inteligente.

### Estrutura

| Arquivo | Conteúdo |
|---------|----------|
| `test_smart_search.py` | SmartSearchService, SearchDictionaryManager, direct/dictionary/fuzzy/spellcheck/learning |
| `test_normalization.py` | `normalize_name_for_search` |
| `test_service_integration.py` | Integração com serviço Product |

### Fixtures (conftest.py)

- `redis_client`: Cliente Redis (host=localhost, port=666, db=0)
- `clean_redis`: Redis limpo antes/depois de cada teste
- `product_objects`: Manager de produtos (com bootstrap)
- `dictionary_manager`: SearchDictionaryManager
- `smart_search_service`: SmartSearchService
- `sample_products`: 6 produtos de exemplo
- `heineken_products`: 3 produtos Heineken (typos)

### Comandos

```bash
# Todos os testes
uv run pytest redis_testing/om/product/tests/

# Com cobertura
uv run pytest redis_testing/om/product/tests/ -vv --cov=redis_testing.om.product --cov-report=term

# Apenas normalização
uv run pytest redis_testing/om/product/tests/test_normalization.py
```

### Pré-requisitos

- Redis (redis-stack) na porta 666 — `docker compose up -d`
- **db=0** obrigatório (RediSearch)

### Documentação detalhada

Ver [redis_testing/om/product/tests/README.md](../../redis_testing/om/product/tests/README.md) para cobertura completa e exemplos de comandos parametrizados.
