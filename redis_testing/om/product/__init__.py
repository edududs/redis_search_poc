from .manager import ProductOMObjects
from .model import ProductOM
from .service import Product
from .service import product as product_service
from .utils import gerar_produtos_fake

__all__ = [
    "Product",
    "ProductOM",
    "ProductOMObjects",
    "gerar_produtos_fake",
    "product_service",
]
