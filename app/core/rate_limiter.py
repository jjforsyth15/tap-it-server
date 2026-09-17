import os

from slowapi import Limiter

from app.core.client_ip import get_client_ip

RATE_LIMIT_STORAGE_URL = os.getenv("RATE_LIMIT_STORAGE_URL", "memory://")

limiter = Limiter(key_func=get_client_ip, storage_uri=RATE_LIMIT_STORAGE_URL)
