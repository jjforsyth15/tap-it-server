from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True}

@router.get("/hello")
def hello():
    return {"message": "Hello, World!"}