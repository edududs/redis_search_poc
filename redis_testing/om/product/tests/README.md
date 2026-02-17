# Testes de Busca Inteligente

Este diretório contém testes abrangentes para o sistema de busca inteligente implementado no módulo `smart_search`.

## Estrutura dos Testes

### `test_smart_search.py`

Testes principais para `SmartSearchService` e `SearchDictionaryManager`:

- **TestSearchDictionaryManager**: Testes do gerenciador de dicionário Redis
- **TestSmartSearchServiceDirectSearch**: Testes de busca direta
- **TestSmartSearchServiceDictionarySearch**: Testes de busca com dicionário
- **TestSmartSearchServiceFuzzySearch**: Testes de busca fuzzy
- **TestSmartSearchServiceSpellcheck**: Testes de spellchecking
- **TestSmartSearchServiceLearning**: Testes de aprendizado automático
- **TestSmartSearchServiceEdgeCases**: Testes de casos limite
- **TestSmartSearchServiceIntegration**: Testes de integração
- **TestSmartSearchServicePerformance**: Testes de performance
- **TestSmartSearchServiceIndexResolution**: Testes de resolução de índice

### `test_normalization.py`

Testes para a função `normalize_name_for_search`:

- Remoção de acentos
- Remoção de stopwords
- Normalização de maiúsculas
- Limite de comprimento
- Remoção de duplicatas
- Tratamento de caracteres especiais

### `test_service_integration.py`

Testes de integração com o serviço `Product`:

- Busca através do serviço
- Retorno de objetos ProductOM
- Múltiplas queries
- Aprendizado ao longo do tempo

## Executando os Testes

### Pré-requisitos

- Redis (redis-stack) rodando na porta 666 — `docker compose up -d`
- **db=0** — RediSearch só suporta índices no database 0 (ver `conftest.py`)
- Python 3.13+
- Dependências instaladas (`pytest`, `redis`, `redis-om`)

### Executar todos os testes

```bash
uv run pytest redis_testing/om/product/tests/
```

### Executar testes específicos

```bash
# Apenas testes de busca direta
uv run pytest redis_testing/om/product/tests/test_smart_search.py::TestSmartSearchServiceDirectSearch

# Apenas testes de normalização
uv run pytest redis_testing/om/product/tests/test_normalization.py

# Teste específico
uv run pytest redis_testing/om/product/tests/test_smart_search.py::TestSmartSearchServiceDirectSearch::test_direct_search_finds_products
```

### Executar com cobertura

```bash
uv run pytest redis_testing/om/product/tests/ --cov=redis_testing.om.product --cov-report=html
```

### Executar com verbose

```bash
uv run pytest redis_testing/om/product/tests/ -v
```

### Executar apenas testes parametrizados específicos

```bash
uv run pytest redis_testing/om/product/tests/test_smart_search.py::TestSmartSearchServiceDirectSearch::test_direct_search_finds_products["cerveja skol-1-direct"]
```

## Cobertura de Testes

Os testes cobrem:

1. **Busca Direta** (8+ casos)
   - Queries exatas
   - Limites de resultados
   - Queries vazias
   - Stopwords apenas

2. **Busca com Dicionário** (3+ casos)
   - Mapeamento completo
   - Mapeamento parcial
   - Sem correspondência

3. **Busca Fuzzy** (5+ casos)
   - Tolerância a erros de digitação
   - Múltiplos tokens
   - Aprendizado automático

4. **Spellcheck** (2+ casos)
   - Extração de sugestões
   - Tratamento de erros

5. **Aprendizado Automático** (4+ casos)
   - Tokens de mesmo comprimento
   - Tokens de comprimentos diferentes
   - Threshold de similaridade
   - Construção de vocabulário

6. **Casos Limite** (10+ casos)
   - Queries vazias/inválidas
   - Limites diferentes
   - Queries muito longas
   - Normalização integrada

7. **Integração** (5+ casos)
   - Fluxo completo de busca
   - Estrutura de metadata
   - Consistência entre buscas

8. **Normalização** (15+ casos parametrizados)
   - Acentos, stopwords, maiúsculas
   - Caracteres especiais
   - Preposições, medidas
   - Duplicatas, ordem

## Configuração Redis (conftest.py)

- `host="localhost"`, `port=666`, **`db=0`**
- `bootstrap()` é chamado em `product_objects` para criar índices

## Fixtures Disponíveis

- `redis_client`: Cliente Redis para testes
- `clean_redis`: Redis limpo antes/depois de cada teste
- `product_objects`: Manager de produtos
- `dictionary_manager`: Gerenciador de dicionário
- `smart_search_service`: Serviço de busca inteligente
- `sample_products`: Produtos de exemplo para testes

## Notas

- Os testes usam **db=0** (único database que suporta índices RediSearch). Configuração em `conftest.py`.
- Cada teste limpa o Redis (`flushdb`) antes e depois da execução
- Os testes são independentes e podem ser executados em qualquer ordem
- Testes parametrizados permitem cobrir múltiplos cenários com menos código
