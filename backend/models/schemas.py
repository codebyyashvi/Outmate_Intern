# models/schemas.py
from pydantic import BaseModel

class EnrichRequest(BaseModel):
    prompt: str