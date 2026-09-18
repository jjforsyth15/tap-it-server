import os
from ipaddress import ip_address

from fastapi import Request


UNKNOWN_CLIENT_IP = "unknown"


def get_client_ip(request: Request) -> str:
    """Return the trusted client IP for rate limiting and request logging."""
    if os.getenv("RENDER", "").lower() == "true":
        connecting_ip = request.headers.get("cf-connecting-ip")

        if not connecting_ip:
            return UNKNOWN_CLIENT_IP

        try:
            return str(ip_address(connecting_ip.strip()))
        except ValueError:
            return UNKNOWN_CLIENT_IP

    if request.client:
        return request.client.host

    return UNKNOWN_CLIENT_IP
