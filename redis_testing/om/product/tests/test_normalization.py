"""Tests for name normalization functionality."""

from __future__ import annotations

import pytest

from redis_testing.name_normalization import normalize_name_for_search


class TestNormalizeNameForSearch:
    """Tests for normalize_name_for_search function."""

    @pytest.mark.parametrize(
        ("input_name", "expected"),
        [
            ("Café de Leite 200 ml", "CAFE LEITE"),
            ("cafe café Leite", "CAFE LEITE"),
            ("Caixa de Leite Integral 1L", "CAIXA LEITE INTEGRAL"),
            ("Açúcar Cristal 1kg", "ACUCAR CRISTAL"),
            ("Cerveja Skol 350ml", "CERVEJA SKOL"),
            ("Leite de Vaca", "LEITE VACA"),
            ("Produto para Casa", "PRODUTO CASA"),
            ("Café & Açúcar", "CAFE ACUCAR"),
        ],
    )
    def test_normalize_removes_accents_and_stopwords(
        self,
        input_name: str,
        expected: str,
    ) -> None:
        """Test normalization removes accents and stopwords."""
        result = normalize_name_for_search(input_name)
        assert result == expected

    @pytest.mark.parametrize(
        "input_name",
        [
            "",
            "   ",
            "\t\n",
            "de",
            "da",
            "do",
            "1",
            "kg",
            "ml",
            "350ml",
            "1kg",
        ],
    )
    def test_normalize_empty_or_stopwords_only(self, input_name: str) -> None:
        """Test normalization with empty or stopwords-only input."""
        result = normalize_name_for_search(input_name)
        assert result == ""

    @pytest.mark.parametrize(
        ("input_name", "expected_contains"),
        [
            ("Café", "CAFE"),
            ("Açúcar", "ACUCAR"),
            ("Leite", "LEITE"),
            ("Cerveja", "CERVEJA"),
        ],
    )
    def test_normalize_uppercase(self, input_name: str, expected_contains: str) -> None:
        """Test normalization converts to uppercase."""
        result = normalize_name_for_search(input_name)
        assert result == expected_contains

    @pytest.mark.parametrize(
        ("input_name", "expected_length"),
        [
            ("Café", 4),
            ("Cerveja Skol", 12),  # "CERVEJA SKOL" = 12 chars
            ("Leite de Vaca", 10),
            ("A" * 300, 200),
        ],
    )
    def test_normalize_length_limit(self, input_name: str, expected_length: int) -> None:
        """Test normalization respects length limit."""
        result = normalize_name_for_search(input_name)
        assert len(result) <= 200
        if expected_length <= 200:
            assert len(result) == expected_length

    def test_normalize_removes_duplicates(self) -> None:
        """Test normalization removes duplicate tokens."""
        result = normalize_name_for_search("cafe cafe leite")
        assert result == "CAFE LEITE"
        assert result.count("CAFE") == 1

    @pytest.mark.parametrize(
        ("input_name", "expected"),
        [
            ("Produto-123", "PRODUTO"),
            ("Café@Açúcar", "CAFE ACUCAR"),
            ("Leite#Vaca", "LEITE VACA"),
            ("Cerveja$Skol", "CERVEJA SKOL"),
        ],
    )
    def test_normalize_removes_special_characters(
        self,
        input_name: str,
        expected: str,
    ) -> None:
        """Test normalization removes special characters."""
        result = normalize_name_for_search(input_name)
        assert result == expected

    @pytest.mark.parametrize(
        ("input_name", "expected"),
        [
            ("Café de Leite", "CAFE LEITE"),
            ("Produto para Casa", "PRODUTO CASA"),
            ("Cerveja com Limão", "CERVEJA LIMAO"),
            ("Açúcar sem Adoçante", "ACUCAR ADOCANTE"),
        ],
    )
    def test_normalize_removes_prepositions(
        self,
        input_name: str,
        expected: str,
    ) -> None:
        """Test normalization removes Portuguese prepositions."""
        result = normalize_name_for_search(input_name)
        assert result == expected

    @pytest.mark.parametrize(
        ("input_name", "expected"),
        [
            ("Café 200g", "CAFE"),
            ("Leite 1L", "LEITE"),
            ("Açúcar 500g", "ACUCAR"),
            ("Produto 350ml", "PRODUTO"),
        ],
    )
    def test_normalize_removes_measurements(
        self,
        input_name: str,
        expected: str,
    ) -> None:
        """Test normalization removes measurement units."""
        result = normalize_name_for_search(input_name)
        assert result == expected

    def test_normalize_preserves_order(self) -> None:
        """Test normalization preserves token order."""
        result = normalize_name_for_search("Cerveja Brahma Premium")
        assert result == "CERVEJA BRAHMA PREMIUM"
        assert result.split()[0] == "CERVEJA"
        assert result.split()[1] == "BRAHMA"
        assert result.split()[2] == "PREMIUM"

    @pytest.mark.parametrize(
        "input_name",
        [
            "a",
            "b",
            "1",
            "2",
            "x",
        ],
    )
    def test_normalize_removes_single_characters(self, input_name: str) -> None:
        """Test normalization removes single character tokens."""
        result = normalize_name_for_search(input_name)
        assert result == ""

    def test_normalize_case_insensitive_input(self) -> None:
        """Test normalization handles case-insensitive input."""
        result1 = normalize_name_for_search("CAFÉ")
        result2 = normalize_name_for_search("café")
        result3 = normalize_name_for_search("Café")
        assert result1 == result2 == result3 == "CAFE"
