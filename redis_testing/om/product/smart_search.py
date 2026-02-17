# ruff: noqa: D102, D107, PLR2004

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Any

from redis.exceptions import RedisError

from redis_testing.name_normalization import normalize_name_for_search

if TYPE_CHECKING:
    from redis import Redis

    from .manager import ProductOMObjects
    from .model import ProductOM


DICTIONARY_KEY = "search-words-dictionary"
MIN_LEARN_RATIO = 0.6


@dataclass(frozen=True)
class SmartSearchMeta:
    based_in: str
    find_by: str
    strategy: str

    def to_dict(self) -> dict[str, str]:
        return {
            "based_in": self.based_in,
            "find_by": self.find_by,
            "strategy": self.strategy,
        }


class SearchDictionaryManager:
    """Manage search-term rewrites backed by Redis hash."""

    def __init__(self, client: Redis, key: str = DICTIONARY_KEY) -> None:
        self._client = client
        self._key = key

    @staticmethod
    def _normalize_word(word: str) -> str:
        return normalize_name_for_search(word).strip().upper()

    def get(self, word: str) -> str | None:
        lookup = self._normalize_word(word)
        if not lookup:
            return None
        value = self._client.hget(self._key, lookup)
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode()
        return value

    def set(self, source_word: str, target_word: str) -> None:
        source = self._normalize_word(source_word)
        target = self._normalize_word(target_word)
        if not source or not target:
            return
        if source_word.strip() == target_word.strip():
            return
        self._client.hset(self._key, source, target)

    def rewrite_query(self, normalized_query: str) -> str:
        rewritten_tokens = [self.get(token) or token for token in normalized_query.split()]
        return " ".join(rewritten_tokens).strip()


class SmartSearchService:
    """Orchestrate direct search, dictionary rewrite, fuzzy search and spellcheck."""

    def __init__(
        self,
        client: Redis,
        objects: ProductOMObjects,
        model: type[ProductOM],
        *,
        dictionary: SearchDictionaryManager | None = None,
    ) -> None:
        self._client = client
        self._objects = objects
        self._model = model
        self._dictionary = dictionary or SearchDictionaryManager(client)

    def search(
        self,
        query: str,
        limit: int = 100,
    ) -> tuple[list[ProductOM], dict[str, str]]:
        limit = max(limit, 0)
        normalized_query = normalize_name_for_search(query)
        if not normalized_query:
            return ([], SmartSearchMeta(query, "", "empty").to_dict())

        direct = self._search_direct(normalized_query, limit=limit)
        if direct:
            return (
                direct,
                SmartSearchMeta(query, normalized_query, "direct").to_dict(),
            )

        dictionary_query = self._dictionary.rewrite_query(normalized_query)
        if dictionary_query and dictionary_query != normalized_query:
            dictionary_matches = self._search_direct(dictionary_query, limit=limit)
            if dictionary_matches:
                return (
                    dictionary_matches,
                    SmartSearchMeta(query, dictionary_query, "dictionary").to_dict(),
                )

        fuzzy_matches, fuzzy_query = self._search_fuzzy(normalized_query, limit=limit)
        if fuzzy_matches:
            self._learn(normalized_query, fuzzy_query, fuzzy_matches)
            return (
                fuzzy_matches,
                SmartSearchMeta(query, fuzzy_query, "fuzzy").to_dict(),
            )

        suggestion = self._spellcheck_suggestion(normalized_query)
        if suggestion and suggestion != normalized_query:
            suggestion_matches = self._search_direct(suggestion, limit=limit)
            if suggestion_matches:
                self._learn(normalized_query, suggestion, suggestion_matches)
                return (
                    suggestion_matches,
                    SmartSearchMeta(query, suggestion, "spellcheck").to_dict(),
                )

        return ([], SmartSearchMeta(query, normalized_query, "not_found").to_dict())

    def _search_direct(self, normalized_query: str, *, limit: int) -> list[ProductOM]:
        return self._objects.find_by_name_search(normalized_query, limit=limit)

    def _search_fuzzy(
        self,
        normalized_query: str,
        *,
        limit: int,
    ) -> tuple[list[ProductOM], str]:
        # Use one and then two percent pairs to increase Levenshtein distance.
        for wrapper in ("%", "%%"):
            matches_by_id: dict[str, ProductOM] = {}
            for token in normalized_query.split():
                fuzzy_token = f"{wrapper}{token}{wrapper}"
                for product in self._objects.find_by_name_search(
                    fuzzy_token,
                    limit=limit,
                ):
                    product_identifier = getattr(product, "pk", product.id)
                    matches_by_id[product_identifier] = product
            if matches_by_id:
                return (list(matches_by_id.values())[:limit], normalized_query)
        return ([], normalized_query)

    def _learn(
        self,
        source_query: str,
        target_query: str,
        matches: list[ProductOM],
    ) -> None:
        source_tokens = source_query.split()
        target_tokens = target_query.split()
        vocabulary = self._build_vocabulary(matches)

        if (
            source_tokens
            and target_tokens
            and len(source_tokens) == len(target_tokens)
            and source_query != target_query
        ):
            for source_token, target_token in zip(
                source_tokens,
                target_tokens,
                strict=True,
            ):
                if source_token != target_token and target_token in vocabulary:
                    self._dictionary.set(source_token, target_token)
            return

        for source_token in source_tokens:
            best_token = self._best_match(source_token, vocabulary)
            if best_token and best_token != source_token:
                self._dictionary.set(source_token, best_token)

    @staticmethod
    def _build_vocabulary(matches: list[ProductOM]) -> set[str]:
        vocabulary: set[str] = set()
        for product in matches:
            vocabulary.update(product.name_search.split())
        return vocabulary

    @staticmethod
    def _best_match(source_token: str, candidates: set[str]) -> str | None:
        source = normalize_name_for_search(source_token).strip().upper()
        if not source:
            return None
        best_token: str | None = None
        best_ratio = 0.0
        for candidate in candidates:
            ratio = SequenceMatcher(a=source, b=candidate).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_token = candidate
        if best_ratio >= MIN_LEARN_RATIO:
            return best_token
        return None

    def _spellcheck_suggestion(self, normalized_query: str) -> str | None:
        index_name = self._resolve_index_name()
        if not index_name:
            return None
        try:
            response = self._client.ft(index_name).spellcheck(normalized_query)
        except RedisError:
            return None
        except Exception:
            return None
        return self._extract_spellcheck_suggestion(response)

    def _resolve_index_name(self) -> str | None:
        meta = self._model.Meta
        explicit_index_name = getattr(meta, "index_name", None)
        if explicit_index_name:
            return explicit_index_name

        try:
            raw_list = self._client.execute_command("FT._LIST")
        except RedisError:
            return None
        except Exception:
            return None

        indexes: list[str] = []
        for value in raw_list or []:
            if isinstance(value, bytes):
                indexes.append(value.decode())
            else:
                indexes.append(str(value))

        model_key_prefix = getattr(meta, "model_key_prefix", "")
        global_key_prefix = getattr(meta, "global_key_prefix", "")
        for index in indexes:
            if model_key_prefix and model_key_prefix in index:
                return index
            if global_key_prefix and global_key_prefix in index:
                return index
        return indexes[0] if indexes else None

    @staticmethod
    def _extract_spellcheck_suggestion(response: Any) -> str | None:
        # Response shape varies by redis/redis-py versions; parse conservatively.
        # Common pattern: [total, [term, [[score, suggestion], ...]], ...]
        if not isinstance(response, list):
            return None

        best_suggestion: str | None = None
        best_score = -1.0
        for item in response:
            if not isinstance(item, list) or len(item) < 2:
                continue
            candidates = item[1]
            if not isinstance(candidates, list):
                continue
            for candidate in candidates:
                if not isinstance(candidate, list) or len(candidate) < 2:
                    continue
                raw_score, raw_term = candidate[0], candidate[1]
                try:
                    score = float(raw_score)
                except (TypeError, ValueError):
                    continue
                term = raw_term.decode() if isinstance(raw_term, bytes) else str(raw_term)
                if score > best_score:
                    best_score = score
                    best_suggestion = normalize_name_for_search(term)
        return best_suggestion
