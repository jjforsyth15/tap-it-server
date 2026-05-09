from pydantic import BaseModel
from uuid import UUID

class CardCreate(BaseModel):
    profile_id: UUID
    card_name: str