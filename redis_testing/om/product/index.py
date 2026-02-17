"""ProductOM index with PHONETIC (Double Metaphone) for name_search.

Ensures the product index uses PHONETIC dm:pt on name_search_fts for
phonetic matching (e.g. heikennen -> HEINEKEN). Must run after SchemaDetector
since redis-om does not support PHONETIC natively.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from redis.commands.search.field import NumericField, TagField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType

if TYPE_CHECKING:
    from redis import Redis

INDEX_NAME = "redis-om-testing:product_om:index"
PREFIX = "redis-om-testing:product_om:"
PHONETIC_MATCHER = "dm:pt"


def _product_schema() -> tuple[TextField | TagField | NumericField, ...]:
    """Schema matching redis-om ProductOM, with PHONETIC on name_search_fts."""
    return (
        TagField("$.id", as_name="id", separator="|"),
        TagField("$.name", as_name="name", separator="|"),
        TextField("$.name", as_name="name_fts"),
        TagField("$.name_search", as_name="name_search", separator="|"),
        TextField(
            "$.name_search",
            as_name="name_search_fts",
            phonetic_matcher=PHONETIC_MATCHER,
        ),
        TagField("$.description", as_name="description", separator="|"),
        TextField("$.description", as_name="description_fts"),
        TagField("$.category", as_name="category", separator="|"),
        NumericField("$.price", as_name="price", sortable=True),
    )


def ensure_product_index_with_phonetic(client: Redis) -> None:
    """Create or replace ProductOM index with PHONETIC on name_search.

    SchemaDetector creates the index without PHONETIC. This function drops
    and recreates it with Double Metaphone (dm:pt) for phonetic matching.
    Call after bootstrap() / SchemaDetector.run().
    """
    ft = client.ft(INDEX_NAME)
    definition = IndexDefinition(
        prefix=[PREFIX],
        index_type=IndexType.JSON,
    )
    try:
        ft.info()
    except Exception:
        ft.create_index(
            _product_schema(),
            definition=definition,
        )
        return

    ft.dropindex(delete_documents=False)
    ft.create_index(
        _product_schema(),
        definition=definition,
    )
