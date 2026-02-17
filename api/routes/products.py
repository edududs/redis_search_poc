"""Endpoints de produtos: GET por id (fallback), POST para criar."""

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import get_api_key
from api.deps import get_product_repository
from api.schemas import (
    ProductCreate,
    ProductResponse,
    ProductSearchMeta,
    ProductSearchResponse,
)
from redis_testing.om.product import product_service

if TYPE_CHECKING:
    from api.crud import ProductRepository

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/search")
def search_products(
    q: str,
    _: Annotated[str, Depends(get_api_key)],
    limit: int = 100,
) -> ProductSearchResponse:
    """Search products using the smart search pipeline from Redis."""
    products, metadata = product_service.smart_search(q, limit=limit)
    return ProductSearchResponse(
        meta=ProductSearchMeta(**metadata),
        products=[ProductResponse.model_validate(product) for product in products],
    )


@router.get("/{product_id}")
def get_product(
    product_id: str,
    _: Annotated[str, Depends(get_api_key)],
    repo: Annotated["ProductRepository", Depends(get_product_repository)],
) -> ProductResponse:
    """Retorna produto por id.

    Usado como fallback quando Product.get(
        pk,
        fallback_to_api=True,
    ) não encontra no cache.
    """
    product = repo.get(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado",
        )
    return product


@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    _: Annotated[str, Depends(get_api_key)],
    repo: Annotated["ProductRepository", Depends(get_product_repository)],
) -> ProductResponse:
    existing = repo.get(body.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Produto {body.id} já existe",
        )
    return repo.insert(body)
