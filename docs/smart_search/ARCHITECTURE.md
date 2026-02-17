# Smart Search — Documentação Técnica

Arquitetura e componentes do pipeline de busca inteligente.

## Visão Geral

O Smart Search é um pipeline em camadas que combina Redis (RediSearch), normalização de texto e aprendizado automático para tolerar typos e variações de escrita em buscas de produtos.

## Componentes

### 1. Normalização (`redis_testing/name_normalization.py`)

- **Função**: `normalize_name_for_search(name)` — padroniza nomes para busca.
- **Regras**:
  - Remove acentos (NFKD).
  - Converte para maiúsculas.
  - Remove caracteres não alfanuméricos.
  - Remove stopwords (preposições, unidades, números).
  - Remove tokens de 1 caractere.
  - Deduplica tokens.
  - Limita a 200 caracteres.
- **Exemplo**: `"Café de Leite 200 ml"` → `"CAFE LEITE"`.

### 2. Modelo ProductOM (`redis_testing/om/product/model.py`)

- **Tipo**: `JsonModel` (redis-om) com `index=True`.
- **Campos indexados**:
  - `name_search`: full-text, usado na busca.
  - `name`, `description`, `category`: full-text/index.
  - `price`: sortable.
- **Meta**: `model_key_prefix`, `global_key_prefix`, `database`.

### 2.1 Índice ProductOM com PHONETIC (`redis_testing/om/product/index.py`)

- **Função**: `ensure_product_index_with_phonetic(client)` — recria o índice com PHONETIC no `name_search_fts`.
- **Implementação**: usa `client.ft()` (redis-py) com `TextField(phonetic_matcher="dm:pt")` (Double Metaphone para português).
- **Ordem**: executado após `SchemaDetector`, pois redis-om não suporta PHONETIC nativamente.
- **Efeito**: buscas em `name_search` passam a considerar termos foneticamente similares (ex.: "Jon" ↔ "John").

### 3. Manager ProductOMObjects (`redis_testing/om/product/manager.py`)

- **Responsabilidade**: CRUD e buscas em ProductOM.
- **Métodos relevantes**:
  - `create()`: cria produto e preenche `name_search` via normalização.
  - `find_by_name_search(query, limit)`: busca por `name_search` usando operador `%` (RediSearch).

### 4. SearchDictionaryManager (`redis_testing/om/product/smart_search.py`)

- **Backend**: Redis Hash `search-words-dictionary`.
- **Função**: mapear termos incorretos → termos corretos.
- **Métodos**:
  - `get(word)`: retorna mapeamento ou `None`.
  - `set(source, target)`: grava mapeamento (normaliza ambos).
  - `rewrite_query(normalized_query)`: reescreve tokens usando o dicionário.

### 5. SmartSearchService (`redis_testing/om/product/smart_search.py`)

- **Pipeline** (Waterfall Search, ordem de tentativa):
  1. **Direct**: busca em `name_search` (inclui match fonético via PHONETIC dm:pt).
  2. **Dictionary**: reescreve query com dicionário (typos/sinônimos) e busca.
  3. **Fuzzy**: busca com `%token%` (Levenshtein 1) ou `%%token%%` (Levenshtein 2).
  4. **Spellcheck**: usa `FT.SPELLCHECK` do RediSearch.
  5. **Learn**: ao encontrar via fuzzy/spellcheck, grava mapeamento no dicionário.
- **Retorno**: `(list[ProductOM], dict)` com `based_in`, `find_by`, `strategy`.
- **Constantes**: `MIN_LEARN_RATIO = 0.6` (similaridade mínima para aprender).

### 6. Bootstrap (`redis_testing/om/utils.py`)

- **Função**: `bootstrap(client)` — configura `Meta.database`, cria índices via `SchemaDetector` e aplica PHONETIC no índice ProductOM.
- **Chamada**: no `__init__` do serviço `Product` e nos testes.

### 7. Serviço Product (`redis_testing/om/product/service.py`)

- **Responsabilidade**: orquestrar bootstrap, CRUD, populate e smart search.
- **Métodos**:
  - `smart_search(query, limit)`: delega para `SmartSearchService.search()`.
  - `populate(n, id_prefix, seed)`: cria produtos fake via `gerar_produtos_fake`.
  - `clear()`: remove todos os documentos do modelo.

## Fluxo de Dados

```
Query do usuário
    → normalize_name_for_search()
    → SmartSearchService.search()
        → _search_direct() [exato + fonético via PHONETIC]
        → dictionary.rewrite_query() + _search_direct()
        → _search_fuzzy() [%token% Levenshtein]
        → _spellcheck_suggestion() + _search_direct()
        → _learn() [se fuzzy/spellcheck encontrou]
    → (products, metadata)
```

## Redis

- **Imagem**: `redis/redis-stack:latest` (RediSearch incluído).
- **Porta**: 666 (mapeada de 6379).
- **Database**: apenas db 0 suporta índices RediSearch.
- **Chaves**:
  - Produtos: `redis-om-testing:product_om:{id}`.
  - Dicionário: Hash `search-words-dictionary`.

## API

- **Endpoint**: `GET /products/search?q={query}&limit={n}`.
- **Auth**: header `Authorization: Bearer <API_KEY>`.
- **Resposta**: `ProductSearchResponse` com `meta` (strategy, find_by, based_in) e `products`.
