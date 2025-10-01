import logging
from typing import List, Dict, Any
from database import supabase

app_logger = logging.getLogger(__name__)

def search_similar_documents(query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Busca documentos similares en la tabla 'documents' usando similitud coseno.

    Args:
        query_embedding: Vector de embedding para la consulta (lista de floats).
        limit: Número máximo de resultados a retornar (default 5).

    Returns:
        Lista de diccionarios con 'id', 'content', 'similarity' (distancia coseno).
    """
    try:
        app_logger.info(f"Searching similar documents with query_embedding length: {len(query_embedding)}, limit: {limit}")
        # Usar RPC para la búsqueda de similitud coseno
        response = supabase.rpc('search_similar_documents', {'query_embedding': query_embedding, 'limit_param': limit}).execute()
        app_logger.info(f"RPC response data length: {len(response.data) if response.data else 0}")

        results = []
        for item in response.data:
            results.append({
                'id': item['id'],
                'content': item['content'],
                'similarity': item['similarity']
            })

        app_logger.info(f"Found {len(results)} similar documents")
        return results

    except Exception as e:
        app_logger.error(f"Error searching similar documents: {str(e)}")
        raise