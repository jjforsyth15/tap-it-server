from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import cards
from app.routes import auth
from app.routes import profiles
from app.routes import users
from app.routes import analytics
from app.routes import profile_links
import os
from dotenv import load_dotenv 

load_dotenv()
TEAM_ID = os.getenv("TEAM_ID")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
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