from fastapi import FastAPI
from app.routes import cards
from app.routes import auth

app = FastAPI()

app.include_router(cards.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "TapIt API running"}


@app.get("/login")
def fake_login(next: str | None = None):
    return {
        "message": "Login page placeholder",
        "next": next
    }