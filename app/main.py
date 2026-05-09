from fastapi import FastAPI
from app.routes import cards

app = FastAPI()

app.include_router(cards.router)

@app.get("/")
def root():
    return {"message": "TapIt API running"}


@app.get("/login")
def fake_login(next: str | None = None):
    return {
        "message": "Login page placeholder",
        "next": next
    }