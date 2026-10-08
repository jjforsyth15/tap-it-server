import os
from dotenv import load_dotenv
import jwt as pyjwt
from jwt import PyJWKClient

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_JWT_AUD = os.getenv("SUPABASE_JWT_AUD", "authenticated")
# Supabase's fixed "iss" format -- see vault Decisions re: custom domains.
SUPABASE_JWT_ISSUER = f"{SUPABASE_URL}/auth/v1" if SUPABASE_URL else None
SUPABASE_ALGORITHMS = ("RS256", "ES256")

jwks_client = (
    PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json")
    if SUPABASE_URL
    else None
)


def decode_supabase_token(token: str) -> dict | None:
    if jwks_client is None:
        return None

    try:
        header = pyjwt.get_unverified_header(token)
    except pyjwt.PyJWTError:
        return None

    # Pre-filter only, not a trust decision -- avoids a JWKS lookup for
    # tokens that can't be ours (see vault Decisions for why this matters).
    if header.get("alg") not in SUPABASE_ALGORITHMS or not header.get("kid"):
        return None

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return pyjwt.decode(
            token,
            signing_key.key,
            algorithms=list(SUPABASE_ALGORITHMS),
            audience=SUPABASE_JWT_AUD,
            issuer=SUPABASE_JWT_ISSUER,
            options={"require": ["exp", "sub", "iss", "iat"]},
        )
    except pyjwt.PyJWTError:
        return None
