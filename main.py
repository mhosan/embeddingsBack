import logging
from fastapi import FastAPI, HTTPException, logger, Path, Query
from fastapi.responses import HTMLResponse, JSONResponse
from schemas import Contact, TextRequest, EmbeddingResponse
from constants import MODEL_NAME, MODEL_DIMENSIONS, MAX_SEQUENCE_LENGTH, MODEL_DESCRIPTION, MODEL_USE_CASE, MODEL_LANGUAGE
from database import supabase

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
app.version = "0.1.1"

from hf_client import get_embeddings_from_hf, HF_API_URL, HF_TOKEN

# ============================================
# Endpoint raiz
# ============================================
@app.get('/', tags=['Home'])
def message():
    """ 
        Get sin parametros a la ruta raiz.
        Devuelve un mensaje de bienvenida.
    """
    return HTMLResponse(content="""
    <h3 style='text-align: center; 
    font-family: Arial; 
    margin-top: 10%;'>
    Backend FastAPI para generar embeddings con Hugging Face. <br><br>
    Swagger: .../docs <br>
    </h3>
    """, status_code=200)
 
    
# ============================================
# Endpoint de información sobre el modelo
# ============================================
@app.get("/model-info", tags=['Embeddings'])
async def model_info():
    """
    Información sobre el modelo de embeddings utilizado
    """
    return {
        "model_name": MODEL_NAME,
        "dimensions": MODEL_DIMENSIONS,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "description": MODEL_DESCRIPTION,
        "use_case": MODEL_USE_CASE,
        "language": MODEL_LANGUAGE
    }


# ============================================
# Endpoint de info sobre la salud del modelo
# ============================================
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
            "model": MODEL_NAME,
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

# ============================================================
# Endpoint para generar un embedding a partir de UN solo texto 
# ============================================================
@app.post("/embedding", tags=['Embeddings'])
async def create_single_embedding(text: str):
    """
    Crear embedding para UN SOLO TEXTO (endpoint simplificado)
    - **text**: String para convertir a embedding
    """
    try:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="text cannot be empty")
        
        embeddings = await get_embeddings_from_hf([text.strip()])
        
        return {
            "embedding": embeddings[0] if embeddings else [],
            "text": text.strip(),
            "count": len(embeddings),
            "model": MODEL_NAME,
            "dimensions": len(embeddings[0]) if embeddings else 0
        }
        """ return JSONResponse(content={"message": "Embedding created", 
                                     "model": "BAAI/bge-small-en-v1.5",
                                     "count": len(embeddings),
                                     "texto original": text,
                                     "data": embeddings}, status_code=200)   """
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error in create_single_embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# =======================================================
# Endpoint para generar embeddings de una lista de textos
# =======================================================
@app.post("/embeddings", response_model=EmbeddingResponse, tags=['Embeddings'])
async def create_embeddings(request: TextRequest):
    """
    Crear embeddings para una LISTA de textos
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
        
        return JSONResponse(content={"message": "Embeddings created",
                                     "model": MODEL_NAME,
                                     "count": len(embeddings),
                                     "texto original": request.texts,
                                     "data": embeddings}, status_code=200)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        app_logger.error(f"Error in create_embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



contactos = [
    {"id": 1, "nombre": "Juan", "email": "juan@example.com"},
    {"id": 2, "nombre": "María", "email": "maria@example.com"},
    {"id": 3, "nombre": "Pedro", "email": "pedro@example.com"}
]

@app.get('/contact', tags=['Contactos -test-']) 
def getAllContact():
    """ 
    Get sin parametros pero a la ruta /contact.
    Devuelve todos los contactos.
    """
    return JSONResponse(content=contactos, status_code=200)


@app.get('/contact/{id}', tags=['Contactos -test-']) 
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


@app.get('/contact/', tags=['Contactos -test-'])  
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


@app.post('/contact', tags=['Contactos -test-'])
def addContact(contact: Contact):
    """
    Post con parametro de body (payload).
    Añade un contacto a la base de datos.
    """
    try:
        response = supabase.table('contacts').insert(contact.dict()).execute()
        return JSONResponse(content={"message": "Contacto añadido correctamente", "contact": response.data[0]}, status_code=201)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar contacto: {str(e)}")


@app.put('/contact/{id}', tags=['Contactos -test-'])
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


@app.delete('/contact/{id}', tags=['Contactos -test-'])
def deleteContact(id: int):
    """ 
    Delete con parametro de path.
    Elimina un contacto por su ID.
    """
    for item in contactos:
        if item["id"] == id:
            contactos.remove(item)
            return JSONResponse(content={"message": "Contacto eliminado correctamente", "contact": item}, status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
# test_hf_direct.py