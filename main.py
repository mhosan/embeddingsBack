import logging
from fastapi import FastAPI, HTTPException, logger, Path, Query
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List
import os
import aiohttp
import asyncio
from schemas import Contact, TextRequest, EmbeddingResponse

# ============================================
# CARGAR .ENV SI EXISTE (SOLO LOCAL)
# ============================================
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Development: Loaded .env file")
except ImportError:
    print("✓ Production: Using system environment variables")



app_logger = logging.getLogger(__name__)

app = FastAPI()
app.title = "Embeddings con FastAPI"
app.version = "0.0.1"

contactos = [
    {"id": 1, "nombre": "Juan", "email": "juan@example.com"},
    {"id": 2, "nombre": "María", "email": "maria@example.com"},
    {"id": 3, "nombre": "Pedro", "email": "pedro@example.com"}
]

@app.get('/', tags=['Home'])
def message():
    """ 
        Get sin parametros a la ruta raiz.
        Devuelve un mensaje de bienvenida.
    """
    return HTMLResponse(content=
    "<h1>Hola mundo desde FastAPI</h1>",
    status_code=200)


@app.get('/contact', tags=['Contact']) 
def getAllContact():
    """ 
    Get sin parametros pero a la ruta /contact.
    Devuelve todos los contactos.
    """
    return JSONResponse(content=contactos, status_code=200)


@app.get('/contact/{id}', tags=['Contact']) 
def getContact(id: int = Path(ge=1, le=1000)):
    """ 
    Get con parametro de path.
    Devuelve un contacto por su ID.
    Se valida que el ID esté entre 1 y 1000 con Path
    """
    for item in contactos:
        if item["id"] == id:
            return JSONResponse(content=item, status_code=200)
    return JSONResponse(content=[], status_code=404)


@app.get('/contact/', tags=['Contact'])  
def getContactByName(name: str=Query(min_length=3, max_length=50)):
    """ 
    Get con parametro de query.
    La barra del final es para indicar que se va a recibir un parametro de tipo query.
    Se valida que el nombre tenga entre 3 y 50 caracteres con Query
    Devuelve un contacto por su nombre.
    """
    for item in contactos:
        if item["nombre"] == name:
            return item
    return []


@app.post('/contact', tags=['Contact'])
def addContact(contact: Contact):
    """ 
    Post con parametro de body (payload).
    Añade un contacto.
    """
    contactos.append(contact)
    return JSONResponse(content={"message": "Contacto añadido correctamente", "contact": contact}, status_code=201)


@app.put('/contact/{id}', tags=['Contact'])
def updateContact(id: int, contact: Contact):
    """ 
    Put con parametro de path y body (payload).
    Actualiza un contacto por su ID.
    """
    for item in contactos:
        if item["id"] == id:
            item["nombre"] = contact.nombre
            item["email"] = contact.email
            item["instagram"] = contact.instagram
            return JSONResponse(content={"message": "Contacto añadido correctamente", "contact": contact}, status_code=201)


@app.delete('/contact/{id}', tags=['Contact'])
def deleteContact(id: int):
    """ 
    Delete con parametro de path.
    Elimina un contacto por su ID.
    """
    for item in contactos:
        if item["id"] == id:
            contactos.remove(item)
            return JSONResponse(content={"message": "Contacto eliminado correctamente", "contact": item}, status_code=200)


## ====================================================================
## ====================================================================
# Inicializar cliente de Hugging Face
# Configuración
# HF_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/paraphrase-MiniLM-L6-v2"
HF_API_URL = "https://api-inference.huggingface.co/models/BAAI/bge-small-en-v1.5"
HF_TOKEN = os.getenv("HF_TOKEN")  
if not HF_TOKEN:
    app_logger.error("HF_TOKEN environment variable is not set!")
    raise ValueError("HF_TOKEN environment variable is required")
app_logger.info(f"HF Token loaded: {HF_TOKEN[:10]}..." if HF_TOKEN else "No token")


async def get_embeddings_from_hf(texts: List[str]) -> List[List[float]]:  #esto usa aiohttp y no necesita huggingface_hub
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": texts,
        "options": {
            "wait_for_model": True, # Espera si el modelo está cargándose
            "use_cache": True
        }
    }
    
    app_logger.info(f"Requesting embeddings for {len(texts)} texts")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                HF_API_URL, 
                headers=headers, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                app_logger.info(f"HF API response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    app_logger.info(f"Successfully got embeddings: {len(result)} embeddings")
                    return result
                
                elif response.status == 503:
                    error_text = await response.text()
                    logger.warning(f"Model loading (503): {error_text}")
                    raise HTTPException(
                        status_code=503, 
                        detail="Model is loading. Please try again in a few moments."
                    )
                
                else:
                    error_text = await response.text()
                    app_logger.error(f"HF API error {response.status}: {error_text}")
                    raise HTTPException(
                        status_code=response.status, 
                        detail=f"HuggingFace API error: {error_text}"
                    )
                    
        except asyncio.TimeoutError:
            app_logger.error("Timeout connecting to Hugging Face API")
            raise HTTPException(
                status_code=504, 
                detail="Timeout connecting to Hugging Face API"
            )
        except Exception as e:
            app_logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Unexpected error: {str(e)}"
            )

@app.post("/embeddings", response_model=EmbeddingResponse, tags=['Embeddings'])
async def create_embeddings(request: TextRequest):
    """
    Crear embeddings para una lista de textos
    - **texts**: Lista de strings para convertir a embeddings
    Retorna embeddings de 384 dimensiones para cada texto.
    """
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="texts list cannot be empty")
        
        if len(request.texts) > 50:  # Límite razonable
            raise HTTPException(status_code=400, detail="Maximum 50 texts allowed per request")

        app_logger.info(f"Processing {len(request.texts)} texts for embeddings")

        embeddings = await get_embeddings_from_hf(request.texts)
        
        return EmbeddingResponse(
            embeddings=embeddings,
            model="BAAI/bge-small-en-v1.5",
            count=len(embeddings)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        app_logger.error(f"Error in create_embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/embedding", tags=['Embeddings'])
async def create_single_embedding(text: str):
    """
    Crear embedding para un solo texto (endpoint simplificado)
    - **text**: String para convertir a embedding
    """
    try:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="text cannot be empty")
        
        embeddings = await get_embeddings_from_hf([text.strip()])
        
        return {
            "embedding": embeddings[0] if embeddings else [],
            "text": text.strip(),
            "model": "BAAI/bge-small-en-v1.5",
            "dimensions": len(embeddings[0]) if embeddings else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error in create_single_embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health", tags=['Embeddings'])
async def health_check():
    """
    Verificar el estado de la API y conexión con Hugging Face
    """
    try:
        # Test simple con un texto pequeño
        test_result = await get_embeddings_from_hf(["test"])
        
        return {
            "status": "healthy",
            "model": "BAAI/bge-small-en-v1.5",
            "api_url": HF_API_URL,
            "token_configured": bool(HF_TOKEN),
            "test_embedding_dimensions": len(test_result[0]) if test_result else 0
        }
    except Exception as e:
        app_logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "token_configured": bool(HF_TOKEN)
        }

# Endpoint de información sobre el modelo
@app.get("/model-info", tags=['Embeddings'])
async def model_info():
    """
    Información sobre el modelo de embeddings utilizado
    """
    return {
        "model_name": "BAAI/bge-small-en-v1.5",
        "dimensions": 384,
        "max_sequence_length": 5126,
        "description": "Sentence embedding model, maps sentences to 384 dimensional dense vectors",
        "use_case": "Semantic similarity, clustering, semantic search",
        "language": "English (optimized), but works reasonably with other languages"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
# test_hf_direct.py