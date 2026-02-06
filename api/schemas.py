"""Esquemas Pydantic alinhados com UserOM e ProductOM do redis_testing."""

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Tipos reutilizáveis e restrições
StrRequired = Annotated[str, Field(min_length=1, strip_whitespace=True)]
CpfStr = Annotated[str, Field(min_length=11, max_length=11, strip_whitespace=True)]
PositiveInt = Annotated[int, Field(ge=0)]
PositiveFloat = Annotated[float, Field(ge=0.0)]
StrictPositiveFloat = Annotated[float, Field(gt=0.0)]


class UserBase(BaseModel):
    """Campos comuns de usuário."""

    name: StrRequired = Field(description="Nome do usuário")
    email: EmailStr = Field(description="Endereço de email do usuário")
    cpf: CpfStr = Field(description="CPF do usuário (11 dígitos)")
    age: PositiveInt = Field(default=0, description="Idade do usuário")
    weight: PositiveFloat = Field(default=0.0, description="Peso do usuário em kg")
    height: StrictPositiveFloat = Field(
        default=0.1, description="Altura do usuário em metros"
    )


class UserCreate(UserBase):
    """Payload para criação de usuário."""

    id: StrRequired = Field(description="Chave primária (user_id)")
    name: str = Field(default="", description="Nome do usuário")


class UserResponse(UserBase):
    """Resposta com dados do usuário."""

    id: StrRequired
    model_config = ConfigDict(from_attributes=True)

    @field_validator("cpf", mode="before")
    @classmethod
    def normalize_cpf(cls, v: str) -> str:
        """Reduz CPF a 11 dígitos antes da validação."""
        if not isinstance(v, str):
            return v
        digits = re.sub(r"\D", "", v)
        return digits[:11].zfill(11)


class ProductBase(BaseModel):
    """Campos comuns de produto."""

    name: StrRequired = Field(description="Nome do produto")
    description: StrRequired = Field(description="Descrição do produto")
    category: StrRequired = Field(description="Categoria do produto")
    price: PositiveFloat = Field(default=0.0, description="Preço do produto")


class ProductCreate(ProductBase):
    """Payload para criação de produto."""

    id: StrRequired = Field(description="Chave primária (product_id)")


class ProductResponse(ProductBase):
    """Resposta com dados do produto."""

    id: StrRequired
    model_config = ConfigDict(from_attributes=True)
