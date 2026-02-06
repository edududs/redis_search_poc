from ..utils import get_redis_client
from . import demo_product, demo_user

if __name__ == "__main__":
    client = get_redis_client()
    demo_user(client)
    print()
    demo_product(client)
