"""Gerador de produtos falsos para testes.

Gera nomes de produtos realistas (tipo + modelo/característica), descrição, categoria e preço.
"""

import random
from typing import Iterator

from faker import Faker

_faker = Faker("pt_BR")

CATEGORIAS = [
    "eletrônicos",
    "periféricos",
    "livros",
    "casa",
    "esportes",
    "beleza",
    "brinquedos",
    "alimentos",
]

# Nomes de produtos por categoria: soam como nomes reais de loja.
PRODUTOS_POR_CATEGORIA: dict[str, list[str]] = {
    "eletrônicos": [
        "Notebook Gamer 15.6",
        "Monitor LED 27 polegadas",
        "Smart TV 55 polegadas 4K",
        "Tablet 10 polegadas",
        "Smartwatch com GPS",
        "Fone de ouvido bluetooth",
        "Caixa de som portátil",
        "Webcam Full HD",
        "Carregador wireless",
        "Power bank 20000mAh",
    ],
    "periféricos": [
        "Teclado mecânico RGB",
        "Mouse gamer 16000 DPI",
        "Headset com microfone",
        "Webcam 1080p",
        "Hub USB 3.0 7 portas",
        "Suporte para notebook",
        "Mouse pad gamer XXL",
        "Switch de teclado mecânico",
    ],
    "livros": [
        "Livro de programação Python",
        "Romance best-seller",
        "Enciclopédia infantil",
        "Guia de viagem",
        "Receitas culinárias",
        "Dicionário de idiomas",
    ],
    "casa": [
        "Liquidificador 2L",
        "Air fryer 5L",
        "Cafeteira espresso",
        "Aspirador de pó",
        "Ferro de passar",
        "Jogo de panelas",
    ],
    "esportes": [
        "Bola de futebol oficial",
        "Corda de pular",
        "Luva de goleiro",
        "Tênis de corrida",
        "Garrafa térmica 1L",
        "Colchonete para exercícios",
    ],
    "beleza": [
        "Secador de cabelo",
        "Barbeador elétrico",
        "Kit de maquiagem",
        "Creme hidratante",
        "Perfume 100ml",
    ],
    "brinquedos": [
        "Quebra-cabeça 1000 peças",
        "Carrinho de controle remoto",
        "Boneca articulada",
        "Jogo de tabuleiro",
        "Pelúcia 40cm",
    ],
    "alimentos": [
        "Café em grãos 500g",
        "Chocolate ao leite 200g",
        "Granola natural 400g",
        "Azeite extra virgem 500ml",
        "Mel puro 300g",
    ],
}

PRICE_MIN, PRICE_MAX = 9.90, 9999.90


def _nome_produto_aleatorio() -> tuple[str, str]:
    """Escolhe uma categoria e um nome de produto dessa categoria. Retorna (name, category)."""
    category = random.choice(CATEGORIAS)
    names = PRODUTOS_POR_CATEGORIA[category]
    base = random.choice(names)
    if random.random() < 0.3:
        sufixo = (
            f" {random.randint(1, 99)}"
            if random.random() < 0.5
            else f" {_faker.first_name()}"
        )
        return (f"{base}{sufixo}".strip(), category)
    return (base, category)


def gerar_produtos_fake(
    quantidade: int,
    id_prefix: str = "prod",
    seed: int | None = None,
) -> Iterator[dict]:
    """Gera `quantidade` produtos falsos.

    Args:
        quantidade: Número de produtos a gerar.
        id_prefix: Prefixo do id (ex.: "prod" -> prod-1, prod-2, ...).
        seed: Seed opcional para reprodutibilidade.

    Yields:
        Dicionários com: id, name, description, category, price.

    """
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)

    for i in range(quantidade):
        product_id = f"{id_prefix}-{i + 1}"
        name, category = _nome_produto_aleatorio()
        description = _faker.sentence(nb_words=6) or "Produto de qualidade."
        price = round(random.uniform(PRICE_MIN, PRICE_MAX), 2)

        yield {
            "id": product_id,
            "name": name,
            "description": description,
            "category": category,
            "price": price,
        }
