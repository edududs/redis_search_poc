"""Integration tests for Product service with smart search."""

from __future__ import annotations

import pytest
from redis import Redis

from redis_testing.om.product.manager import ProductOMObjects
from redis_testing.om.product.model import ProductOM
from redis_testing.om.product.service import Product


class TestProductServiceSmartSearch:
    """Tests for Product service smart search integration."""

    def test_smart_search_via_service(
        self,
        clean_redis: Redis,
        sample_products: list[ProductOM],
    ) -> None:
        """Test smart search through Product service."""
        service = Product(client=clean_redis)
        results, metadata = service.smart_search("cerveja", limit=100)
        assert isinstance(results, list)
        assert isinstance(metadata, dict)
        assert "strategy" in metadata
        assert len(results) >= 2

    def test_smart_search_returns_product_objects(
        self,
        clean_redis: Redis,
        sample_products: list[ProductOM],
    ) -> None:
        """Test smart search returns ProductOM objects."""
        service = Product(client=clean_redis)
        results, _ = service.smart_search("cerveja skol", limit=100)
        assert len(results) >= 1
        assert all(isinstance(p, ProductOM) for p in results)
        assert all(hasattr(p, "id") for p in results)
        assert all(hasattr(p, "name_search") for p in results)

    @pytest.mark.parametrize(
        ("query", "expected_min_count"),
        [
            ("cerveja", 2),
            ("cafe", 1),
            ("leite", 1),
            ("acucar", 1),
        ],
    )
    def test_smart_search_multiple_queries(
        self,
        clean_redis: Redis,
        sample_products: list[ProductOM],
        query: str,
        expected_min_count: int,
    ) -> None:
        """Test smart search with multiple different queries."""
        service = Product(client=clean_redis)
        results, metadata = service.smart_search(query, limit=100)
        assert len(results) >= expected_min_count
        assert metadata["strategy"] in ("direct", "fuzzy", "dictionary", "spellcheck")

    def test_smart_search_learns_over_time(
        self,
        clean_redis: Redis,
        product_objects: ProductOMObjects,
    ) -> None:
        """Test smart search learns mappings over multiple searches."""
        service = Product(client=clean_redis)

        product_objects.create(
            product_id="prod-learn-service",
            name="Cerveja Brahma",
            description="Test",
            category="bebidas",
            name_search="CERVEJA BRAHMA",
            price=3.80,
        )

        query = "cerveja"
        results1, metadata1 = service.smart_search(query, limit=100)
        results2, metadata2 = service.smart_search(query, limit=100)

        assert len(results1) == len(results2)
        assert metadata1["strategy"] == metadata2["strategy"]
