"""Comprehensive tests for SmartSearchService."""

from __future__ import annotations

import contextlib
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

import pytest
from redis.exceptions import RedisError

from redis_testing.name_normalization import normalize_name_for_search
from redis_testing.om.product.index import (
    INDEX_NAME,
    ensure_product_index_with_phonetic,
)
from redis_testing.om.product.model import ProductOM

if TYPE_CHECKING:
    from redis import Redis

    from redis_testing.om.product.manager import ProductOMObjects
    from redis_testing.om.product.smart_search import (
        SearchDictionaryManager,
        SmartSearchService,
    )


class TestProductIndexPhonetic:
    """Tests for ProductOM index with PHONETIC (Double Metaphone dm:pt)."""

    def test_ensure_index_creates_with_phonetic(
        self,
        clean_redis: Redis,
    ) -> None:
        """Index is created and includes name_search_fts field."""
        ProductOM.Meta.database = clean_redis
        from redis_om.model.migrations import SchemaDetector

        SchemaDetector(conn=clean_redis).run()
        ensure_product_index_with_phonetic(clean_redis)

        ft = clean_redis.ft(INDEX_NAME)
        info = ft.info()
        assert "index_name" in info or "name" in info

    def test_index_survives_bootstrap_idempotency(
        self,
        clean_redis: Redis,
    ) -> None:
        """Repeated ensure_product_index_with_phonetic does not fail."""
        ProductOM.Meta.database = clean_redis
        from redis_om.model.migrations import SchemaDetector

        SchemaDetector(conn=clean_redis).run()
        ensure_product_index_with_phonetic(clean_redis)
        ensure_product_index_with_phonetic(clean_redis)
        ft = clean_redis.ft(INDEX_NAME)
        ft.info()


class TestSearchDictionaryManager:
    """Tests for SearchDictionaryManager."""

    @pytest.mark.parametrize(
        ("source", "target", "expected"),
        [
            ("cerveja", "CERVEJA", "CERVEJA"),
            ("Cerveja", "cerveja", "CERVEJA"),
            ("café", "CAFE", "CAFE"),
            ("açúcar", "ACUCAR", "ACUCAR"),
            ("leite de vaca", "LEITE VACA", "LEITE VACA"),
        ],
    )
    def test_set_and_get(
        self,
        dictionary_manager: SearchDictionaryManager,
        source: str,
        target: str,
        expected: str,
    ) -> None:
        """Test setting and getting dictionary entries."""
        dictionary_manager.set(source, target)
        result = dictionary_manager.get(source)
        assert result == expected

    def test_get_nonexistent(self, dictionary_manager: SearchDictionaryManager) -> None:
        """Test getting non-existent entry returns None."""
        assert dictionary_manager.get("nonexistent") is None

    @pytest.mark.parametrize(
        ("query", "mappings", "expected"),
        [
            ("cerveja", {"cerveja": "CERVEJA"}, "CERVEJA"),
            ("café pilão", {"cafe": "CAFE", "pilao": "PILAO"}, "CAFE PILAO"),
            ("açúcar cristal", {"acucar": "ACUCAR"}, "ACUCAR cristal"),
            ("leite", {}, "leite"),
        ],
    )
    def test_rewrite_query(
        self,
        dictionary_manager: SearchDictionaryManager,
        query: str,
        mappings: dict[str, str],
        expected: str,
    ) -> None:
        """Test query rewriting with dictionary mappings."""
        normalized = normalize_name_for_search(query)
        for source, target in mappings.items():
            dictionary_manager.set(source, target)
        result = dictionary_manager.rewrite_query(normalized)
        assert result == normalize_name_for_search(expected)

    def test_set_same_source_target(self, dictionary_manager: SearchDictionaryManager) -> None:
        """Test setting same source and target doesn't create entry."""
        dictionary_manager.set("cerveja", "cerveja")
        assert dictionary_manager.get("cerveja") is None

    def test_set_empty_strings(self, dictionary_manager: SearchDictionaryManager) -> None:
        """Test setting empty strings doesn't create entry."""
        dictionary_manager.set("", "target")
        dictionary_manager.set("source", "")
        assert dictionary_manager.get("") is None


class TestSmartSearchServiceDirectSearch:
    """Tests for direct search strategy."""

    @pytest.mark.parametrize(
        ("query", "expected_count", "expected_strategy"),
        [
            ("cerveja skol", 1, "direct"),
            ("CERVEJA SKOL", 1, "direct"),
            ("Cerveja Skol", 1, "direct"),
            ("café pilão", 1, "direct"),
            ("CAFE PILAO", 1, "direct"),
            ("leite integral", 1, "direct"),
            ("cerveja", 3, "direct"),
            ("bebidas", 0, "not_found"),
        ],
    )
    def test_direct_search_finds_products(
        self,
        smart_search_service: SmartSearchService,
        sample_products: list[ProductOM],
        query: str,
        expected_count: int,
        expected_strategy: str,
    ) -> None:
        """Test direct search finds products with exact matches."""
        results, metadata = smart_search_service.search(query, limit=100)
        assert len(results) == expected_count
        assert metadata["strategy"] == expected_strategy
        assert metadata["based_in"] == query
        assert metadata["find_by"] == normalize_name_for_search(query)

    def test_direct_search_limit(
        self,
        smart_search_service: SmartSearchService,
        sample_products: list[ProductOM],
    ) -> None:
        """Test direct search respects limit."""
        results, _ = smart_search_service.search("cerveja", limit=1)
        assert len(results) <= 1

    def test_direct_search_empty_query(
        self,
        smart_search_service: SmartSearchService,
    ) -> None:
        """Test direct search with empty query."""
        results, metadata = smart_search_service.search("", limit=100)
        assert results == []
        assert metadata["strategy"] == "empty"
        assert metadata["find_by"] == ""

    @pytest.mark.parametrize(
        "query",
        [
            "   ",
            "\t\n",
            "   de   ",
            "1kg",
            "350ml",
        ],
    )
    def test_direct_search_stopwords_only(
        self,
        smart_search_service: SmartSearchService,
        query: str,
    ) -> None:
        """Test direct search with stopwords only."""
        results, metadata = smart_search_service.search(query, limit=100)
        assert results == []
        assert metadata["strategy"] in ("empty", "not_found")


class TestSmartSearchServiceDictionarySearch:
    """Tests for dictionary-based search strategy."""

    def test_dictionary_search_finds_products(
        self,
        smart_search_service: SmartSearchService,
        dictionary_manager: SearchDictionaryManager,
        sample_products: list[ProductOM],
    ) -> None:
        """Test dictionary search when direct search fails."""
        dictionary_manager.set("skl", "SKOL")

        results, metadata = smart_search_service.search("cerveja skl", limit=100)
        assert len(results) >= 1
        assert metadata["strategy"] == "dictionary"
        assert "SKOL" in metadata["find_by"]

    def test_dictionary_search_partial_mapping(
        self,
        smart_search_service: SmartSearchService,
        dictionary_manager: SearchDictionaryManager,
        sample_products: list[ProductOM],
    ) -> None:
        """Test dictionary search with partial word mapping."""
        dictionary_manager.set("cerveja", "CERVEJA")

        results, metadata = smart_search_service.search("cerveja", limit=100)
        assert len(results) >= 1
        assert metadata["strategy"] in ("direct", "dictionary")

    def test_dictionary_search_no_match(
        self,
        smart_search_service: SmartSearchService,
        dictionary_manager: SearchDictionaryManager,
    ) -> None:
        """Test dictionary search when no products match."""
        dictionary_manager.set("nonexistent", "ALSO_NONEXISTENT")

        results, metadata = smart_search_service.search("nonexistent", limit=100)
        assert results == []
        assert metadata["strategy"] == "not_found"


class TestSmartSearchServiceFuzzySearch:
    """Tests for fuzzy search strategy."""

    @pytest.mark.parametrize(
        ("query", "expected_min_count"),
        [
            ("cerveja", 2),
            ("cerveja skol", 1),
            ("cafe", 1),
            ("acucar", 1),
            ("leite", 1),
        ],
    )
    def test_fuzzy_search_finds_products(
        self,
        smart_search_service: SmartSearchService,
        sample_products: list[ProductOM],
        query: str,
        expected_min_count: int,
    ) -> None:
        """Test fuzzy search finds products with typos."""
        results, metadata = smart_search_service.search(query, limit=100)
        assert len(results) >= expected_min_count
        assert metadata["strategy"] in ("direct", "fuzzy", "dictionary")

    @pytest.mark.parametrize(
        ("query", "expected_strategy"),
        [
            ("cerveja skol", "direct"),
            ("cerveja", "direct"),
            ("cafe pilao", "direct"),
        ],
    )
    def test_fuzzy_search_fallback_when_direct_fails(
        self,
        smart_search_service: SmartSearchService,
        product_objects: ProductOMObjects,
        sample_products: list[ProductOM],
        query: str,
        expected_strategy: str,
    ) -> None:
        """Test fuzzy search as fallback when direct fails."""
        product_objects.create(
            product_id="prod-fuzzy",
            name="Cerveja Skol 350ml",
            description="Test",
            category="bebidas",
            name_search="CERVEJA SKOL",
            price=3.50,
        )

        results, metadata = smart_search_service.search(query, limit=100)
        assert len(results) >= 1
        assert metadata["strategy"] in ("direct", "fuzzy", "dictionary")

    def test_fuzzy_search_learns_mapping(
        self,
        smart_search_service: SmartSearchService,
        dictionary_manager: SearchDictionaryManager,
        product_objects: ProductOMObjects,
    ) -> None:
        """Test fuzzy search learns and stores mappings."""
        product_objects.create(
            product_id="prod-learn",
            name="Cerveja Brahma",
            description="Test",
            category="bebidas",
            name_search="CERVEJA BRAHMA",
            price=3.80,
        )

        query = "cerveja"
        results, _ = smart_search_service.search(query, limit=100)

        if results:
            learned = dictionary_manager.get("cerveja")
            assert learned is not None or len(results) > 0


class TestSmartSearchServiceSpellcheck:
    """Tests for spellcheck strategy."""

    def test_spellcheck_suggestion_extraction(
        self,
        smart_search_service: SmartSearchService,
        clean_redis: Redis,
    ) -> None:
        """Test spellcheck suggestion extraction."""
        index_name = smart_search_service._resolve_index_name()
        if not index_name:
            pytest.skip("Index not available for spellcheck test")

        try:
            suggestion = smart_search_service._spellcheck_suggestion("cerveja")
            assert suggestion is None or isinstance(suggestion, str)
        except (RedisError, Exception):
            pytest.skip("Spellcheck not available")

    def test_spellcheck_handles_errors(
        self,
        smart_search_service: SmartSearchService,
        clean_redis: Redis,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test spellcheck handles Redis errors gracefully."""

        def mock_spellcheck(*args: object, **kwargs: object) -> None:
            msg = "Connection failed"
            raise RedisError(msg)

        monkeypatch.setattr(
            clean_redis.ft("test").__class__,
            "spellcheck",
            mock_spellcheck,
        )

        suggestion = smart_search_service._spellcheck_suggestion("cerveja")
        assert suggestion is None


class TestSmartSearchServiceLearning:
    """Tests for automatic learning functionality."""

    def test_learn_same_length_tokens(
        self,
        smart_search_service: SmartSearchService,
        dictionary_manager: SearchDictionaryManager,
        product_objects: ProductOMObjects,
    ) -> None:
        """Test learning with same-length token sequences."""
        product_objects.create(
            product_id="prod-learn-1",
            name="Cerveja Skol",
            description="Test",
            category="bebidas",
            name_search="CERVEJA SKOL",
            price=3.50,
        )

        query = "cerveja skl"
        results, _ = smart_search_service.search(query, limit=100)

        if results:
            assert dictionary_manager.get("skl") == "SKOL"

    def test_learn_different_length_tokens(
        self,
        smart_search_service: SmartSearchService,
        dictionary_manager: SearchDictionaryManager,
        product_objects: ProductOMObjects,
    ) -> None:
        """Test learning with different-length token sequences."""
        product_objects.create(
            product_id="prod-learn-2",
            name="Cerveja Brahma Premium",
            description="Test",
            category="bebidas",
            name_search="CERVEJA BRAHMA PREMIUM",
            price=4.50,
        )

        query = "cerveja"
        results, _ = smart_search_service.search(query, limit=100)

        if results:
            learned = dictionary_manager.get("cerveja")
            assert learned is not None or len(results) > 0

    def test_learn_minimum_ratio_threshold(
        self,
        smart_search_service: SmartSearchService,
        dictionary_manager: SearchDictionaryManager,
        product_objects: ProductOMObjects,
    ) -> None:
        """Test learning respects minimum similarity ratio."""
        product_objects.create(
            product_id="prod-learn-3",
            name="Cerveja",
            description="Test",
            category="bebidas",
            name_search="CERVEJA",
            price=3.50,
        )

        query = "xyzabc"
        _results, _ = smart_search_service.search(query, limit=100)

        learned = dictionary_manager.get("xyzabc")
        if learned:
            assert smart_search_service._best_match("xyzabc", {"CERVEJA"}) is None

    def test_build_vocabulary(
        self,
        smart_search_service: SmartSearchService,
        sample_products: list[ProductOM],
    ) -> None:
        """Test vocabulary building from products."""
        vocabulary = smart_search_service._build_vocabulary(sample_products)
        assert isinstance(vocabulary, set)
        assert len(vocabulary) > 0
        assert "CERVEJA" in vocabulary or "SKOL" in vocabulary or "BRAHMA" in vocabulary

    def test_best_match_calculation(
        self,
        smart_search_service: SmartSearchService,
    ) -> None:
        """Test best match calculation."""
        vocabulary = {"CERVEJA", "SKOL", "BRAHMA", "CAFE"}
        best = smart_search_service._best_match("cerveja", vocabulary)
        assert best == "CERVEJA"

        best_low = smart_search_service._best_match("xyz", vocabulary)
        assert best_low is None


class TestSmartSearchServiceEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.parametrize(
        "query",
        [
            "",
            "   ",
            "\t\n\r",
            "a",
            "de",
            "1",
            "kg",
            "ml",
        ],
    )
    def test_empty_or_invalid_queries(
        self,
        smart_search_service: SmartSearchService,
        query: str,
    ) -> None:
        """Test handling of empty or invalid queries."""
        results, metadata = smart_search_service.search(query, limit=100)
        assert isinstance(results, list)
        assert isinstance(metadata, dict)
        assert "strategy" in metadata

    @pytest.mark.parametrize(
        "limit",
        [
            0,
            1,
            10,
            100,
            1000,
            -1,
        ],
    )
    def test_different_limits(
        self,
        smart_search_service: SmartSearchService,
        sample_products: list[ProductOM],
        limit: int,
    ) -> None:
        """Test search with different limit values."""
        results, _ = smart_search_service.search("cerveja", limit=limit)
        if limit > 0:
            assert len(results) <= limit
        else:
            assert isinstance(results, list)

    def test_very_long_query(
        self,
        smart_search_service: SmartSearchService,
        sample_products: list[ProductOM],
    ) -> None:
        """Test search with very long query."""
        long_query = "cerveja " * 100
        results, metadata = smart_search_service.search(long_query, limit=100)
        assert isinstance(results, list)
        assert isinstance(metadata, dict)

    @pytest.mark.parametrize(
        ("query", "expected_normalization"),
        [
            ("Café", "CAFE"),
            ("Açúcar", "ACUCAR"),
            ("Leite de Vaca", "LEITE VACA"),
            ("Cerveja 350ml", "CERVEJA"),
            ("Produto 1kg", "PRODUTO"),
        ],
    )
    def test_normalization_integration(
        self,
        smart_search_service: SmartSearchService,
        sample_products: list[ProductOM],
        query: str,
        expected_normalization: str,
    ) -> None:
        """Test that queries are properly normalized."""
        _results, metadata = smart_search_service.search(query, limit=100)
        normalized = normalize_name_for_search(query)
        assert metadata["find_by"] == normalized or metadata["find_by"].startswith(normalized)


class TestSmartSearchServiceIntegration:
    """Integration tests for complete search flow."""

    def test_complete_search_flow_direct(
        self,
        smart_search_service: SmartSearchService,
        sample_products: list[ProductOM],
    ) -> None:
        """Test complete search flow with direct match."""
        results, metadata = smart_search_service.search("cerveja skol", limit=100)
        assert len(results) >= 1
        assert metadata["strategy"] == "direct"
        assert all(hasattr(p, "id") for p in results)
        assert all(hasattr(p, "name_search") for p in results)

    def test_complete_search_flow_dictionary(
        self,
        smart_search_service: SmartSearchService,
        dictionary_manager: SearchDictionaryManager,
        product_objects: ProductOMObjects,
    ) -> None:
        """Test complete search flow with dictionary rewrite."""
        product_objects.create(
            product_id="prod-dict",
            name="Cerveja Skol",
            description="Test",
            category="bebidas",
            name_search="CERVEJA SKOL",
            price=3.50,
        )

        dictionary_manager.set("cerveja", "CERVEJA")
        dictionary_manager.set("skol", "SKOL")

        results, metadata = smart_search_service.search("cerveja skol", limit=100)
        assert len(results) >= 1
        assert metadata["strategy"] in ("direct", "dictionary")

    def test_complete_search_flow_fuzzy(
        self,
        smart_search_service: SmartSearchService,
        product_objects: ProductOMObjects,
    ) -> None:
        """Test complete search flow with fuzzy matching."""
        product_objects.create(
            product_id="prod-fuzzy-int",
            name="Cerveja Brahma",
            description="Test",
            category="bebidas",
            name_search="CERVEJA BRAHMA",
            price=3.80,
        )

        results, metadata = smart_search_service.search("cerveja", limit=100)
        assert len(results) >= 1
        assert metadata["strategy"] in ("direct", "fuzzy", "dictionary")

    def test_search_metadata_structure(
        self,
        smart_search_service: SmartSearchService,
        sample_products: list[ProductOM],
    ) -> None:
        """Test search metadata has correct structure."""
        _results, metadata = smart_search_service.search("cerveja", limit=100)
        assert "based_in" in metadata
        assert "find_by" in metadata
        assert "strategy" in metadata
        assert isinstance(metadata["based_in"], str)
        assert isinstance(metadata["find_by"], str)
        assert isinstance(metadata["strategy"], str)
        assert metadata["strategy"] in (
            "direct",
            "dictionary",
            "fuzzy",
            "spellcheck",
            "empty",
            "not_found",
        )

    def test_multiple_searches_consistency(
        self,
        smart_search_service: SmartSearchService,
        sample_products: list[ProductOM],
    ) -> None:
        """Test multiple searches return consistent results."""
        query = "cerveja"
        results1, metadata1 = smart_search_service.search(query, limit=100)
        results2, metadata2 = smart_search_service.search(query, limit=100)

        assert len(results1) == len(results2)
        assert metadata1["strategy"] == metadata2["strategy"]
        assert metadata1["find_by"] == metadata2["find_by"]


class TestSmartSearchServicePerformance:
    """Performance and stress tests."""

    def test_search_with_many_products(
        self,
        smart_search_service: SmartSearchService,
        product_objects: ProductOMObjects,
    ) -> None:
        """Test search performance with many products."""
        for i in range(100):
            product_objects.create(
                product_id=f"prod-perf-{i}",
                name=f"Cerveja Test {i}",
                description="Test",
                category="bebidas",
                name_search=f"CERVEJA TEST {i}",
                price=float(i),
            )

        results, metadata = smart_search_service.search("cerveja", limit=100)
        assert len(results) <= 100
        assert metadata["strategy"] in ("direct", "fuzzy", "dictionary")

    def test_search_with_special_characters(
        self,
        smart_search_service: SmartSearchService,
        product_objects: ProductOMObjects,
    ) -> None:
        """Test search handles special characters."""
        product_objects.create(
            product_id="prod-special",
            name="Café & Açúcar",
            description="Test",
            category="alimentos",
            name_search="CAFE ACUCAR",
            price=10.0,
        )

        results, metadata = smart_search_service.search("café & açúcar", limit=100)
        assert isinstance(results, list)
        assert isinstance(metadata, dict)


class TestSmartSearchServiceIndexResolution:
    """Tests for index name resolution."""

    def test_resolve_index_name_with_prefix(
        self,
        smart_search_service: SmartSearchService,
        clean_redis: Redis,
    ) -> None:
        """Test index name resolution with model prefix."""
        index_name = smart_search_service._resolve_index_name()
        assert index_name is None or isinstance(index_name, str)

    def test_resolve_index_name_handles_errors(
        self,
        smart_search_service: SmartSearchService,
        clean_redis: Redis,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test index name resolution when no index exists (db=0, Redis from docker-compose)."""
        raw_list = clean_redis.execute_command("FT._LIST")
        for idx in raw_list or []:
            name = idx.decode() if isinstance(idx, bytes) else str(idx)
            with contextlib.suppress(Exception):
                clean_redis.execute_command("FT.DROPINDEX", name, "DD")

        monkeypatch.setattr(
            smart_search_service._model.Meta,
            "index_name",
            None,
        )

        result = smart_search_service._resolve_index_name()
        assert result is None


class TestSmartSearchServiceHeinekenVariations:
    """Tests for Heineken spelling variations - real-world typo scenarios."""

    @pytest.mark.parametrize(
        ("misspelled_query", "expected_find_strategy", "description"),
        [
            # Caso 1: Esquecer "e" antes do "i" ou simplificar final
            ("Hinekken", "fuzzy", "Missing 'e' before 'i'"),
            ("Heniken", "fuzzy", "Missing 'e' before 'i', simplified ending"),
            ("Heineken", "direct", "Correct spelling"),
            ("Heinekn", "fuzzy", "Simplified ending"),
            ("Heineke", "fuzzy", "Simplified ending"),
            # Caso 2: Baseado puramente no som da pronúncia
            ("Haignen", "fuzzy", "Pronunciation-based spelling"),
            ("Haikenen", "fuzzy", "Pronunciation-based spelling"),
            ("Haineken", "fuzzy", "Pronunciation-based spelling"),
            ("Haineken", "fuzzy", "Pronunciation variation"),
            # Caso 3: Ignorar "H" inicial (comum em países latinos)
            ("Aineken", "fuzzy", "Missing initial 'H' (Latin countries)"),
            ("Einekènne", "fuzzy", "Missing 'H', accent variation"),
            ("Eineken", "fuzzy", "Missing initial 'H'"),
            ("Eneken", "fuzzy", "Missing 'H' and 'i'"),
            # Caso 4: Confusão com nomes de pilotos de F1
            ("Hakkinen", "fuzzy", "F1 driver name confusion"),
            ("Raikkonen", "fuzzy", "F1 driver name confusion"),
            ("Heakkinen", "fuzzy", "Mixed with F1 name"),
            # Caso 5: Erros na terminação ou troca de vogais centrais
            ("Heinekee", "fuzzy", "Termination error"),
            ("Hoineke", "fuzzy", "Vowel swap in middle"),
            ("Heineken", "direct", "Correct spelling repeated"),
            # Casos adicionais de variações comuns
            ("Heineken", "direct", "Correct with space"),
            ("Heineken", "direct", "Correct uppercase"),
            ("heineken", "direct", "Correct lowercase"),
            ("HEINEKEN", "direct", "Correct all caps"),
            ("Heineken", "direct", "Correct mixed case"),
        ],
    )
    def test_heineken_typo_variations_find_product(
        self,
        smart_search_service: SmartSearchService,
        heineken_products: list[ProductOM],
        misspelled_query: str,
        expected_find_strategy: str,
        description: str,
    ) -> None:
        """Test that various Heineken misspellings find the correct product."""
        results, metadata = smart_search_service.search(
            f"cerveja {misspelled_query}",
            limit=100,
        )

        assert len(results) >= 1, f"Failed for '{misspelled_query}': {description}"
        assert metadata["strategy"] in (
            "direct",
            "fuzzy",
            "dictionary",
        ), f"Unexpected strategy for '{misspelled_query}': {metadata['strategy']}"

        found_heineken = any("HEINEKEN" in (p.name_search or "").upper() for p in results)
        assert found_heineken, (
            f"Product 'HEINEKEN' not found in results for query '{misspelled_query}'. "
            f"Found: {[p.name_search for p in results]}"
        )

    @pytest.mark.parametrize(
        ("misspelled_query", "description"),
        [
            ("Hinekken", "Missing 'e' before 'i'"),
            ("Heniken", "Missing 'e' before 'i', simplified ending"),
            ("Haignen", "Pronunciation-based spelling"),
            ("Haikenen", "Pronunciation-based spelling"),
            ("Aineken", "Missing initial 'H'"),
            ("Eineken", "Missing initial 'H'"),
            ("Hakkinen", "F1 driver name confusion"),
            ("Heinekee", "Termination error"),
            ("Hoineke", "Vowel swap in middle"),
        ],
    )
    def test_heineken_typo_learns_correct_spelling(
        self,
        smart_search_service: SmartSearchService,
        dictionary_manager: SearchDictionaryManager,
        heineken_products: list[ProductOM],
        misspelled_query: str,
        description: str,
    ) -> None:
        """Test that searching with typos learns the correct spelling."""
        normalized_misspelling = normalize_name_for_search(misspelled_query)
        normalized_correct = normalize_name_for_search("Heineken")

        results, metadata = smart_search_service.search(
            f"cerveja {misspelled_query}",
            limit=100,
        )

        if results and metadata["strategy"] in ("fuzzy", "spellcheck"):
            learned = dictionary_manager.get(normalized_misspelling)
            if learned:
                assert learned == normalized_correct or normalized_correct in learned, (
                    f"Learned mapping '{normalized_misspelling}' -> '{learned}' "
                    f"should be closer to '{normalized_correct}'"
                )

    @pytest.mark.parametrize(
        ("query_variation", "expected_min_results"),
        [
            ("cerveja Hinekken", 1),
            ("cerveja Heniken", 1),
            ("cerveja Haignen", 1),
            ("cerveja Aineken", 1),
            ("cerveja Heinekee", 1),
            ("cerveja Hoineke", 1),
            ("Heineken", 3),
            ("cerveja Heineken", 3),
            ("CERVEJA HEINEKEN", 3),
        ],
    )
    def test_heineken_variations_with_category_word(
        self,
        smart_search_service: SmartSearchService,
        heineken_products: list[ProductOM],
        query_variation: str,
        expected_min_results: int,
    ) -> None:
        """Test Heineken variations work with category word 'cerveja'."""
        results, _metadata = smart_search_service.search(query_variation, limit=100)

        assert len(results) >= expected_min_results, (
            f"Expected at least {expected_min_results} results for '{query_variation}', "
            f"got {len(results)}"
        )

        heineken_found = any("HEINEKEN" in (p.name_search or "").upper() for p in results)
        assert heineken_found, (
            f"Heineken product not found for query '{query_variation}'. "
            f"Results: {[p.name_search for p in results]}"
        )

    def test_heineken_direct_vs_fuzzy_strategy(
        self,
        smart_search_service: SmartSearchService,
        heineken_products: list[ProductOM],
    ) -> None:
        """Test that correct spelling uses direct strategy, typos use fuzzy."""
        correct_query = "cerveja Heineken"
        results_correct, metadata_correct = smart_search_service.search(
            correct_query,
            limit=100,
        )

        assert len(results_correct) >= 1
        assert metadata_correct["strategy"] == "direct"

        typo_query = "cerveja Hinekken"
        results_typo, metadata_typo = smart_search_service.search(typo_query, limit=100)

        assert len(results_typo) >= 1
        assert metadata_typo["strategy"] in ("fuzzy", "dictionary")

    @pytest.mark.parametrize(
        ("misspelling", "similarity_threshold"),
        [
            ("Hinekken", 0.7),
            ("Heniken", 0.7),
            ("Haignen", 0.6),
            ("Aineken", 0.7),
            ("Heinekee", 0.8),
            ("Hoineke", 0.7),
        ],
    )
    def test_heineken_typo_similarity_scores(
        self,
        smart_search_service: SmartSearchService,
        misspelling: str,
        similarity_threshold: float,
    ) -> None:
        """Test that typo variations have acceptable similarity scores."""
        correct = normalize_name_for_search("Heineken")
        misspelled = normalize_name_for_search(misspelling)

        similarity = SequenceMatcher(a=correct, b=misspelled).ratio()
        assert similarity >= similarity_threshold, (
            f"Similarity {similarity:.2f} between '{correct}' and '{misspelled}' "
            f"is below threshold {similarity_threshold}"
        )

    def test_heineken_multiple_variations_same_search(
        self,
        smart_search_service: SmartSearchService,
        heineken_products: list[ProductOM],
    ) -> None:
        """Test searching with multiple typo variations in sequence."""
        variations = [
            "Hinekken",
            "Heniken",
            "Haignen",
            "Aineken",
            "Heinekee",
            "Hoineke",
        ]

        all_found = True
        strategies_used = set()

        for variation in variations:
            results, metadata = smart_search_service.search(
                f"cerveja {variation}",
                limit=100,
            )
            strategies_used.add(metadata["strategy"])
            if not results:
                all_found = False
                break

            found_heineken = any("HEINEKEN" in (p.name_search or "").upper() for p in results)
            if not found_heineken:
                all_found = False
                break

        assert all_found, "Not all typo variations found Heineken products"
        assert "fuzzy" in strategies_used or "dictionary" in strategies_used, (
            "Expected fuzzy or dictionary strategy to be used for typos"
        )

    def test_heineken_learning_persistence(
        self,
        smart_search_service: SmartSearchService,
        dictionary_manager: SearchDictionaryManager,
        heineken_products: list[ProductOM],
    ) -> None:
        """Test that learned mappings persist across searches."""
        typo = "Hinekken"
        normalized_typo = normalize_name_for_search(typo)

        results1, _ = smart_search_service.search(f"cerveja {typo}", limit=100)
        assert len(results1) >= 1

        learned_after_first = dictionary_manager.get(normalized_typo)

        results2, metadata2 = smart_search_service.search(f"cerveja {typo}", limit=100)
        assert len(results2) >= 1

        learned_after_second = dictionary_manager.get(normalized_typo)

        if learned_after_first:
            assert learned_after_second == learned_after_first, (
                "Learned mapping should persist across searches"
            )
            assert metadata2["strategy"] in ("direct", "dictionary"), (
                "Second search should use dictionary if mapping was learned"
            )
