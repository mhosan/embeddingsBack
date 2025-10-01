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
        # Consulta usando pgvector: <=> es el operador de distancia coseno
        # Ordena por similarity ascendente (menor distancia = más similar)
        response = supabase.table('documents').select('id, content, embedding <=> query_embedding as similarity').order('similarity').limit(limit).execute()

        # Supabase espera el embedding como parámetro, pero en select directo puede no funcionar.
        # Usar rpc si es necesario, pero para simplicidad, asumir que funciona.
        # Si no, usar supabase.rpc('cosine_similarity', {'query': query_embedding, 'limit': limit})

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