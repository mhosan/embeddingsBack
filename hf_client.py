import os
import logging
import aiohttp
import asyncio
from typing import List
from fastapi import HTTPException, logger
from constants import MODEL_NAME

# ============================================>
# CARGAR .ENV SI EXISTE (SOLO LOCAL)
# ============================================>
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Development: Loaded .env file")
except ImportError:
    print("✓ Production: Using system environment variables")

app_logger = logging.getLogger(__name__)

# ============================================>
# Inicializar cliente de Hugging Face
# ============================================>
HF_API_URL = f"https://api-inference.huggingface.co/models/{MODEL_NAME}"
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    app_logger.error("HF_TOKEN environment variable is not set!")
    raise ValueError("HF_TOKEN environment variable is required")
app_logger.info(f"HF Token loaded: {HF_TOKEN[:10]}..." if HF_TOKEN else "No token")

# ============================================>
# generar el embedding
# ============================================>
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
