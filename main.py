import logging
from fastapi import FastAPI, HTTPException, logger, Path, Query
from fastapi.responses import HTMLResponse, JSONResponse
from schemas import Contact, TextRequest, EmbeddingResponse, DocumentRecord
from constants import MODEL_NAME, MODEL_DIMENSIONS, MAX_SEQUENCE_LENGTH, MODEL_DESCRIPTION, MODEL_USE_CASE, MODEL_LANGUAGE
from database import supabase
from datetime import datetime

# ============================================
# CARGAR .ENV SI EXISTE (SOLO LOCAL)
# ============================================
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Development: Loaded .env file")
except ImportError:
    print("✓ Production: Using system environment variables")

app_logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ===========================================
# CONFIGURAR CORS
# ===========================================
origins = [
    "https://geoofertas.com.ar",
    "https://www.geoofertas.com.ar",
    "https://udp.com.ar",
    "https://www.udp.com.ar"
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.title = "Embeddings con FastAPI"
app.version = "0.1.9"

from hf_client import get_embeddings_from_hf
from search_service import search_similar_documents

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
def health_check():
    """
    Verificar el estado de la API y conexión con Hugging Face
    """
    try:
        # Test simple con un texto pequeño
        test_result = get_embeddings_from_hf(["test"])
        
        return {
            "status": "healthy",
            "model": MODEL_NAME,
            "test_embedding_dimensions": len(test_result[0]) if test_result else 0
        }
    except Exception as e:
        app_logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# ============================================================
# Endpoint para generar un embedding a partir de UN solo texto 
# ============================================================
@app.post("/embedding", tags=['Embeddings'])
def create_single_embedding(text: str):
    """
    Crear embedding para UN SOLO TEXTO (endpoint simplificado)
    - **text**: String para convertir a embedding
    """
    try:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="El texto no puede estar vacío")
        
        embeddings = get_embeddings_from_hf([text.strip()])

        # Guardar en Supabase
        record = DocumentRecord(
            content=text.strip(),
            embedding=embeddings[0],
            metadata={"model": MODEL_NAME, "timestamp": datetime.utcnow().isoformat()}
        )
        try:
            data_to_insert = record.dict(exclude={'id', 'source', 'created_at'})
            response = supabase.table('documents').insert(data_to_insert).execute()
            document_id = response.data[0]['id']
        except Exception as e:
            app_logger.error(f"Error saving to Supabase: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save document")

        return {
            "embedding": embeddings[0] if embeddings else [],
            "text": text.strip(),
            "count": len(embeddings),
            "model": MODEL_NAME,
            "dimensions": len(embeddings[0]) if embeddings else 0,
            "document_id": document_id
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
def create_embeddings(request: TextRequest):
    """
    Crear embeddings para una LISTA de textos
    - **texts**: Lista de strings para convertir a embeddings
    Retorna embeddings de 384 dimensiones para cada texto.
    """
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="La lista de textos no puede estar vacia")
        
        if len(request.texts) > 2500:  # Límite razonable
            raise HTTPException(status_code=400, detail="Maximum 250 texts allowed per request")

        app_logger.info(f"Processing {len(request.texts)} texts for embeddings")

        embeddings = get_embeddings_from_hf(request.texts)

        # Guardar en Supabase
        document_ids = []
        for i, emb in enumerate(embeddings):
            record = DocumentRecord(
                content=request.texts[i],
                embedding=emb,
                metadata={"model": MODEL_NAME, "timestamp": datetime.utcnow().isoformat()}
            )
            try:
                data_to_insert = record.dict(exclude={'id', 'source', 'created_at'})
                response = supabase.table('documents').insert(data_to_insert).execute()
                document_ids.append(response.data[0]['id'])
            except Exception as e:
                app_logger.error(f"Error saving document {i} to Supabase: {str(e)}")
                document_ids.append(None)  # O manejar de otra forma

        return JSONResponse(content={"message": "Embeddings created",
                                     "model": MODEL_NAME,
                                     "count": len(embeddings),
                                     "texto original": request.texts,
                                     "data": embeddings,
                                     "document_ids": document_ids}, status_code=200)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        app_logger.error(f"Error in create_embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================
# Endpoint para buscar documentos similares
# ============================================
@app.post("/search", tags=['Search'])
def search_documents(text: str, limit: int = Query(5, ge=1, le=20)):
    """
    Buscar documentos similares en la base de datos usando similitud coseno.
    - **text**: Texto de consulta para generar embedding y buscar similares
    - **limit**: Número máximo de resultados (1-20, default 5)
    """
    try:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="El texto no puede estar vacío")

        # Generar embedding del texto de consulta
        embeddings = get_embeddings_from_hf([text.strip()])

        # Buscar documentos similares
        results = search_similar_documents(embeddings[0], limit)

        return {
            "query_text": text.strip(),
            "results": results,
            "model": MODEL_NAME,
            "limit": limit
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error in search_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================
# Endpoint para obtener información de la tabla documents
# ============================================
@app.get("/documents/info", tags=['Documents'])
def documents_info():
    """
    Retorna métricas básicas de la tabla `documents` necesarias para un dashboard:
    - count: cantidad de registros
    - earliest_created_at: fecha del registro más antiguo (created_at)
    - latest_created_at: fecha del registro más reciente (created_at)

    Nota: Implementación mínima usando el cliente `supabase` ya presente en el proyecto.
    """
    try:
        # Obtener cantidad de registros (count exacto)
        count_resp = supabase.table('documents').select('*', count='exact').limit(1).execute()
        total_count = getattr(count_resp, 'count', None)

        # Obtener el registro con la fecha más antigua
        earliest_resp = supabase.table('documents').select('created_at').order('created_at', desc=False).limit(1).execute()
        earliest = earliest_resp.data[0]['created_at'] if earliest_resp.data else None

        # Obtener el registro con la fecha más reciente
        latest_resp = supabase.table('documents').select('created_at').order('created_at', desc=True).limit(1).execute()
        latest = latest_resp.data[0]['created_at'] if latest_resp.data else None

        return {
            'count': total_count,
            'earliest_created_at': earliest,
            'latest_created_at': latest
        }
    except Exception as e:
        app_logger.error(f"Error fetching documents info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ============================================
# Endpoint para obtener los n últimos registros de documents
# ============================================
from fastapi import Query

@app.get("/documents/latest", tags=['Documents'])
def documents_latest(n: int = Query(5, ge=1)):
    """
    Devuelve los n últimos registros de la tabla documents, ordenados por created_at descendente.
    - n: cantidad de registros a devolver (default 5, sin límite máximo)
    """
    try:
        resp = supabase.table('documents').select('*').order('created_at', desc=True).limit(n).execute()
        return {'latest_documents': resp.data}
    except Exception as e:
        app_logger.error(f"Error fetching latest documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ============================================
# Endpoint para obtener los n primeros registros de documents
# ============================================
@app.get("/documents/earliest", tags=['Documents'])
def documents_earliest(n: int = Query(5, ge=1)):
    """
    Devuelve los n primeros registros de la tabla documents, ordenados por created_at ascendente.
    - n: cantidad de registros a devolver (default 5, sin límite máximo)
    """
    try:
        resp = supabase.table('documents').select('*').order('created_at', desc=False).limit(n).execute()
        return {'earliest_documents': resp.data}
    except Exception as e:
        app_logger.error(f"Error fetching earliest documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ============================================
# Endpoint para borrar un registro por id en documents
# ============================================
from fastapi import Path

@app.delete("/documents/{id}", tags=['Documents'])
def delete_document(id: int = Path(..., description="ID del documento a borrar")):
    """
    Elimina un registro de la tabla documents por su id.
    """
    try:
        resp = supabase.table('documents').delete().eq('id', id).execute()
        if resp.data and len(resp.data) > 0:
            return {"deleted": True, "id": id}
        else:
            raise HTTPException(status_code=404, detail=f"Documento con id {id} no encontrado")
    except Exception as e:
        app_logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ============================================
# Endpoint para obtener un rango de registros por id en documents
# ============================================
@app.get("/documents/range", tags=['Documents'])
def documents_range(start_id: int = Query(..., description="ID del registro inicial"), limit: int = Query(..., ge=1, description="Cantidad de registros a recuperar")):
    """
    Devuelve una cantidad específica de registros a partir de un ID inicial.
    - start_id: ID del registro desde donde comenzar
    - limit: Cantidad de registros a recuperar (mínimo 1, sin límite máximo)
    """
    try:
        resp = supabase.table('documents').select('*').gte('id', start_id).order('id', desc=False).limit(limit).execute()
        return {'documents_range': resp.data, 'start_id': start_id, 'limit': limit, 'count': len(resp.data)}
    except Exception as e:
        app_logger.error(f"Error fetching documents range: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
# test_hf_direct.py