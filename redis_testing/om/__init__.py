"""Package Redis OM: HashModel (UserOM), JsonModel (ProductOM), bootstrap e demos."""

from .demo import demo_product, demo_user
from .product import Product, ProductOM, product_service
from .user import User, UserOM, user_service
from .utils import bootstrap

main = demo_user
main_json = demo_product

__all__ = [
    "Product",
    "ProductOM",
    "User",
    "UserOM",
    "bootstrap",
    "demo_product",
    "demo_user",
    "main",
    "main_json",
    "product_service",
    "user_service",
]
