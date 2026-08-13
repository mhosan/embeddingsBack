import logging
import json
from fastapi import FastAPI, HTTPException, logger, Path, Query
from fastapi.responses import HTMLResponse, JSONResponse
from schemas import Contact, TextRequest, EmbeddingResponse, DocumentRecord
from constants import MODEL_NAME, MODEL_DIMENSIONS, MAX_SEQUENCE_LENGTH, MODEL_DESCRIPTION, MODEL_USE_CASE, MODEL_LANGUAGE
from database import get_connection
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
    "https://mhosan.github.io",
    "https://mhosan.github.io/",
    "https://www.mhosan.github.io",
    "https://www.mhosan.github.io/",
    "https://mhosan.github.io/embeddings-front",
    "https://mhosan.github.io/embeddings-front/",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:4200",
    "https://mhtest.alwaysdata.net/embeddings/",
    "https://mhtest.alwaysdata.net/embeddings"
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

        # Guardar en Neon
        embedding_str = "[" + ",".join(str(x) for x in embeddings[0]) + "]"
        metadata = {"model": MODEL_NAME, "timestamp": datetime.utcnow().isoformat()}
        try:
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO documents (content, embedding, metadata) VALUES (%s, %s::vector, %s) RETURNING id;",
                        (text.strip(), embedding_str, json.dumps(metadata))
                    )
                    document_id = cur.fetchone()['id']
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            app_logger.error(f"Error saving to Neon: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save document: {str(e)}")

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

        # Guardar en Neon
        document_ids = []
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                for i, emb in enumerate(embeddings):
                    embedding_str = "[" + ",".join(str(x) for x in emb) + "]"
                    metadata = {"model": MODEL_NAME, "timestamp": datetime.utcnow().isoformat()}
                    try:
                        cur.execute(
                            "INSERT INTO documents (content, embedding, metadata) VALUES (%s, %s::vector, %s) RETURNING id;",
                            (request.texts[i], embedding_str, json.dumps(metadata))
                        )
                        document_ids.append(cur.fetchone()['id'])
                    except Exception as e:
                        app_logger.error(f"Error saving document {i} to Neon: {str(e)}")
                        document_ids.append(None)
            conn.commit()
        finally:
            conn.close()

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
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Cantidad total de registros
                cur.execute("SELECT COUNT(*) AS total FROM documents;")
                total_count = cur.fetchone()['total']

                # Fecha del registro más antiguo
                cur.execute("SELECT created_at FROM documents ORDER BY created_at ASC LIMIT 1;")
                row = cur.fetchone()
                earliest = str(row['created_at']) if row else None

                # Fecha del registro más reciente
                cur.execute("SELECT created_at FROM documents ORDER BY created_at DESC LIMIT 1;")
                row = cur.fetchone()
                latest = str(row['created_at']) if row else None
        finally:
            conn.close()

        return {
            'count': total_count,
            'earliest_created_at': earliest,
            'latest_created_at': latest
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        app_logger.error(f"Error fetching documents info: {str(e)}\n{tb}")
        print(f"TRACEBACK ERROR: {tb}")
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
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, content, metadata, created_at FROM documents ORDER BY created_at DESC LIMIT %s;", (n,))
                rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
        return {'latest_documents': rows}
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
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, content, metadata, created_at FROM documents ORDER BY created_at ASC LIMIT %s;", (n,))
                rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
        return {'earliest_documents': rows}
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
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM documents WHERE id = %s RETURNING id;", (id,))
                deleted_row = cur.fetchone()
            conn.commit()
        finally:
            conn.close()
        if deleted_row:
            return {"deleted": True, "id": id}
        else:
            raise HTTPException(status_code=404, detail=f"Documento con id {id} no encontrado")
    except HTTPException:
        raise
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
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, content, metadata, created_at FROM documents WHERE id >= %s ORDER BY id ASC LIMIT %s;",
                    (start_id, limit)
                )
                rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
        return {'documents_range': rows, 'start_id': start_id, 'limit': limit, 'count': len(rows)}
    except Exception as e:
        app_logger.error(f"Error fetching documents range: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
# test_hf_direct.py