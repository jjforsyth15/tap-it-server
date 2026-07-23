from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import beta, cards, profile_images
from app.routes import auth
from app.routes import profiles
from app.routes import users
from app.routes import analytics
from app.routes import profile_links
import os
import logging
import time
from uuid import uuid4
from dotenv import load_dotenv 
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from app.core.rate_limiter import limiter

load_dotenv()
TEAM_ID = os.getenv("TEAM_ID")
CURRENT_URL = os.getenv("CURRENT_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")
FRONTEND_URL_IP = os.getenv("FRONTEND_URL_IP")

required_env_vars = {
    "CURRENT_URL": CURRENT_URL,
    "FRONTEND_URL": FRONTEND_URL,
}

missing = [name for name, value in required_env_vars.items() if not value]

if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tapit.requests")
logger.setLevel(logging.INFO)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    
    request_id = str(uuid4())
    start_time = time.perf_counter()
    
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "unknown")
    referrer = request.headers.get("referer", "none")
    
    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        logger.info(
            "Request ID: %s | Method: %s | Path: %s | Status: %d | Duration: %s ms | Client IP: %s | Referrer: %s | User-Agent: %s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            client_ip,
            referrer,
            user_agent
        )
        
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        logger.exception(
            "Unexpected application error",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "referrer": referrer,
                "user_agent": user_agent,
            },
        )
        
        response = JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            "Request ID: %s | Method: %s | Path: %s | Status: %d | Duration: %s ms | Client IP: %s | Referrer: %s | User-Agent: %s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            get_client_ip(request),
            request.headers.get("referer", "none"),
            request.headers.get("user-agent", "unknown")
        )
        
        return response


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        FRONTEND_URL_IP,
<<<<<<< HEAD
        "https://tapitcard.org",
        "https://www.tapitcard.org",
        "https://tapit-8386d.web.app",
=======
        "http://localhost:4173",
>>>>>>> develop
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards.router)
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(analytics.router)
app.include_router(profile_links.router)
app.include_router(users.router)
app.include_router(profile_images.router)
app.include_router(beta.router)

@app.get("/")
def root():
    return {"message": "TapIt API running"}


@app.get("/login")
def fake_login(next: str | None = None):
    return {
        "message": "Login page placeholder",
        "next": next
    }
    
    
@app.get("/.well-known/apple-app-site-association")
async def apple_app_site_association():
    return JSONResponse(
        content={
            "applinks": {
                "apps": [],
                "details": [
                    {
                        "appIDs": [f"{TEAM_ID}.org.tapitcard.app"],
                        "components": [{"/": "/cards/*"}]
                    }
                ]
            }
        },
        media_type="application/json"
    )
    

def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-Forwarded-For")
    
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    if request.client:
        return request.client.host
    
    return "unknown"

