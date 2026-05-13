from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routes import cards
from app.routes import auth
from app.routes import profiles
import os
from dotenv import load_dotenv 

load_dotenv()
TEAM_ID = os.getenv("TEAM_ID")

app = FastAPI()

app.include_router(cards.router)
app.include_router(auth.router)
app.include_router(profiles.router)

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