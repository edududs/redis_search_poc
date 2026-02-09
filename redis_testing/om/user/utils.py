"""Gerador de usuários falsos para testes.

Gera dados realistas (nome, email, CPF, idade, peso, altura) com Faker.
Garante que, dentro de um mesmo lote, email e CPF não se repitam — útil para
testar buscas por campo “único” (ex.: find_by_email, find_by_cpf) sem colisões.
"""

import random
from collections.abc import Iterator

from faker import Faker

# Locale pt_BR: nomes e formatos brasileiros. Para CPF usamos geração manual
# para controlar unicidade (Faker pode repetir).
_faker = Faker("pt_BR")

# Faixas realistas para idade, peso (kg) e altura (m).
AGE_MIN, AGE_MAX = 18, 80
WEIGHT_MIN, WEIGHT_MAX = 45.0, 120.0
HEIGHT_MIN, HEIGHT_MAX = 1.50, 2.00


def gerar_usuarios_fake(
    quantidade: int,
    id_prefix: str = "fake",
    seed: int | None = None,
) -> Iterator[dict]:
    """Gera `quantidade` usuários falsos com campos únicos (email, CPF) no lote.

    Email e CPF são gerados de forma determinística por (id_prefix, i) para evitar
    exaustão do Faker.unique e garantir exatamente `quantidade` itens.

    Yields:
        Dicionários com: id, name, email, cpf, age, weight, height.

    """
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)

    for i in range(quantidade):
        user_id = f"{id_prefix}-{i + 1}"
        name = _faker.name()
        email = f"{id_prefix}-{i + 1}@batch.example.com"
        cpf = f"000.{i + 1:03d}.000-{i % 100:02d}"
        age = random.randint(AGE_MIN, AGE_MAX)
        weight = round(random.uniform(WEIGHT_MIN, WEIGHT_MAX), 1)
        height = round(random.uniform(HEIGHT_MIN, HEIGHT_MAX), 2)

        yield {
            "id": user_id,
            "name": name,
            "email": email,
            "cpf": cpf,
            "age": age,
            "weight": weight,
            "height": height,
        }
