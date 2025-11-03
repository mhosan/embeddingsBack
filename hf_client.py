import os
import logging
from typing import List
from fastapi import HTTPException
from huggingface_hub import InferenceClient
from constants import MODEL_NAME

"""
La función get_embeddings_from_hf se invoca desde el archivo main.py en varios endpoints de la API FastAPI:
Endpoint /health: Se usa para verificar la salud del modelo con un texto de prueba simple (["test"]).
Endpoint /embedding: Para generar un embedding de UN SOLO texto proporcionado por el usuario.
Endpoint /embeddings: Para generar embeddings de UNA LISTA de textos enviados en la solicitud.
Endpoint /search: Para generar el embedding del texto de consulta y buscar documentos similares en la base de datos.
"""

# ============================================>
# CARGAR .ENV SI EXISTE (SOLO LOCAL)
# ============================================>
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Development: Loaded .env file")
except ImportError:
    print("✓ Production: Using system environment variables")

app_logger = logging.getLogger(__name__)


# ============================================>
# Inicializar cliente de Hugging Face
# ============================================>
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    app_logger.error("HF_TOKEN environment variable is not set!")
    raise ValueError("HF_TOKEN environment variable is required")

app_logger.info(f"HF Token loaded: {HF_TOKEN[:10]}..." if HF_TOKEN else "No token")
print(f"✓ HF Token cargado correctamente")
print(f"✓ Modelo: {MODEL_NAME}")

# Inicializar InferenceClient
try:
    client = InferenceClient(api_key=HF_TOKEN)
    print(f"✓ InferenceClient inicializado correctamente")
except Exception as e:
    print(f"✗ Error inicializando InferenceClient: {str(e)}")
    raise


# ============================================>
# generar el embedding - FUNCIÓN SÍNCRONA
# ============================================>
def get_embeddings_from_hf(texts: List[str]) -> List[List[float]]:
    """
    Genera embeddings usando InferenceClient.
    FUNCIÓN SÍNCRONA (no async) para evitar problemas con FastAPI.
    
    Args:
        texts: Lista de strings para convertir a embeddings
        
    Returns:
        Lista de embeddings (cada uno es una lista de floats)
    """
    print(f"\n[DEBUG] Requesting embeddings for {len(texts)} texts")
    print(f"[DEBUG] Model: {MODEL_NAME}")
    
    app_logger.info(f"Requesting embeddings for {len(texts)} texts to model {MODEL_NAME}")
    
    try:
        print(f"[DEBUG] Llamando a client.feature_extraction()...")
        
        # Llamada directa síncrona
        result = client.feature_extraction(
            text=texts,
            model=MODEL_NAME
        )
        
        print(f"[SUCCESS] Got embeddings")
        print(f"[DEBUG] Result type: {type(result)}")
        
        # Convertir resultado a lista si es necesario
        if hasattr(result, 'tolist'):
            result = result.tolist()
        
        if isinstance(result, list):
            print(f"[DEBUG] Result length: {len(result)}")
            if len(result) > 0 and isinstance(result[0], list):
                print(f"[DEBUG] First embedding length: {len(result[0])}")
        
        app_logger.info(f"Successfully got embeddings")
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] {type(e).__name__}: {error_msg}")
        
        app_logger.error(f"Error: {error_msg}")
        
        if "503" in error_msg or "loading" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail="Model is loading. Please try again in a few moments."
            )
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail="Timeout connecting to Hugging Face API"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating embeddings: {error_msg}"
            )
