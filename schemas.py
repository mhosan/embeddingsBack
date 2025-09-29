from pydantic import BaseModel, Field
from typing import Optional, List

class Contact(BaseModel):
    id: int=Field(ge=1, le=1000)
    nombre: str = Field(min_length=3, max_length=50)
    email: str = Field(pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    instagram: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "nombre": "Juan Perez",
                "email": "juan@example.com",
                "instagram": "@juanperez"
            }
        }

class TextRequest(BaseModel):
    texts: List[str] = Field(min_items=1, example=["Hola mundo", "FastAPI es genial"])
    
class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]] = Field(..., example=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    model: str
