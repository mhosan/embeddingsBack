from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from typing import Dict, Any

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


class DocumentRecord(BaseModel):
    """Modelo que representa una fila en la tabla `public.documents` en Supabase.

    Campos recomendados:
    - id: identificador (opcional, generado por la BD)
    - content: texto original
    - embedding: vector de floats
    - metadata: diccionario con metadatos opcionales
    - source: origen o URI del documento
    - created_at: timestamp ISO
    """
    id: Optional[int] = Field(None, description="ID de la fila en la tabla (autogenerado)")
    content: str = Field(..., min_length=1, description="Texto del documento")
    embedding: List[float] = Field(..., description="Embedding como lista de floats")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
    source: Optional[str] = Field(None, description="Origen o URI del documento")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación (UTC)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "content": "Este es el texto a indexar.",
                "embedding": [0.01, 0.02, 0.03],
                "metadata": {"author": "Marcos", "lang": "es"},
                "source": "file:///C:/docs/ejemplo.txt",
                "created_at": "2025-10-01T11:00:00Z"
            }
        }
