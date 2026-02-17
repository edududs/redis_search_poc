"""Pytest fixtures for product smart search tests."""

from __future__ import annotations

import pytest
from redis import Redis

from redis_testing.om.product.manager import ProductOMObjects
from redis_testing.om.product.model import ProductOM
from redis_testing.om.product.smart_search import SearchDictionaryManager, SmartSearchService
from redis_testing.om.utils import bootstrap
from redis_testing.utils import get_redis_client


@pytest.fixture(scope="function")
def redis_client() -> Redis:
    """Provide a Redis client for testing."""
    return get_redis_client(host="localhost", port=666, db=0)


@pytest.fixture(scope="function")
def clean_redis(redis_client: Redis) -> Redis:
    """Clean Redis before each test."""
    redis_client.flushdb()
    yield redis_client
    redis_client.flushdb()


@pytest.fixture(scope="function")
def product_objects(clean_redis: Redis) -> ProductOMObjects:
    """Provide ProductOMObjects manager."""
    ProductOM.Meta.database = clean_redis
    bootstrap(clean_redis)  # Create RediSearch indexes
    return ProductOM.objects


@pytest.fixture(scope="function")
def dictionary_manager(clean_redis: Redis) -> SearchDictionaryManager:
    """Provide SearchDictionaryManager."""
    return SearchDictionaryManager(clean_redis)


@pytest.fixture(scope="function")
def smart_search_service(
    clean_redis: Redis,
    product_objects: ProductOMObjects,
) -> SmartSearchService:
    """Provide SmartSearchService instance."""
    return SmartSearchService(
        client=clean_redis,
        objects=product_objects,
        model=ProductOM,
    )


@pytest.fixture(scope="function")
def sample_products(product_objects: ProductOMObjects) -> list[ProductOM]:
    """Create sample products for testing."""
    products = [
        product_objects.create(
            product_id="prod-1",
            name="Cerveja Skol 350ml",
            description="Cerveja gelada",
            category="bebidas",
            name_search="CERVEJA SKOL",
            price=3.50,
        ),
        product_objects.create(
            product_id="prod-2",
            name="Cerveja Brahma 350ml",
            description="Cerveja pilsen",
            category="bebidas",
            name_search="CERVEJA BRAHMA",
            price=3.80,
        ),
        product_objects.create(
            product_id="prod-3",
            name="Café Pilão 500g",
            description="Café torrado e moído",
            category="alimentos",
            name_search="CAFE PILAO",
            price=12.90,
        ),
        product_objects.create(
            product_id="prod-4",
            name="Açúcar Cristal 1kg",
            description="Açúcar refinado",
            category="alimentos",
            name_search="ACUCAR CRISTAL",
            price=4.50,
        ),
        product_objects.create(
            product_id="prod-5",
            name="Leite Integral 1L",
            description="Leite pasteurizado",
            category="laticinios",
            name_search="LEITE INTEGRAL",
            price=5.90,
        ),
        product_objects.create(
            product_id="prod-6",
            name="Cerveja Heineken 350ml",
            description="Cerveja importada holandesa",
            category="bebidas",
            name_search="CERVEJA HEINEKEN",
            price=8.50,
        ),
    ]
    return products


@pytest.fixture(scope="function")
def heineken_products(product_objects: ProductOMObjects) -> list[ProductOM]:
    """Create Heineken products for typo variation tests."""
    products = [
        product_objects.create(
            product_id="heineken-1",
            name="Cerveja Heineken 350ml",
            description="Cerveja importada holandesa",
            category="bebidas",
            name_search="CERVEJA HEINEKEN",
            price=8.50,
        ),
        product_objects.create(
            product_id="heineken-2",
            name="Cerveja Heineken 500ml",
            description="Cerveja importada holandesa garrafa",
            category="bebidas",
            name_search="CERVEJA HEINEKEN",
            price=12.90,
        ),
        product_objects.create(
            product_id="heineken-3",
            name="Cerveja Heineken Long Neck",
            description="Cerveja importada long neck",
            category="bebidas",
            name_search="CERVEJA HEINEKEN LONG NECK",
            price=15.90,
        ),
    ]
    return products
