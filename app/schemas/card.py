from pydantic import BaseModel

class CardCreate(BaseModel):
    card_name: str