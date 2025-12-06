import logging
from typing import List, Dict, Any
from database import execute_query

app_logger = logging.getLogger(__name__)

def search_similar_documents(query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """ ==========================================================================================
    Busca documentos similares en la tabla 'documents' usando similitud coseno.
    Args:
        query_embedding: Vector de embedding para la consulta (lista de floats).
        limit: Número máximo de resultados a retornar (default 5).
    Returns:
        Lista de diccionarios con 'id', 'content', 'similarity' (distancia coseno).
        Usa pgvector direct SQL query.
    =========================================================================================== """
    try:
        app_logger.info(f"Searching similar documents with query_embedding length: {len(query_embedding)}, limit: {limit}")
        
        # Consulta SQL usando operador de distancia coseno (<=>) de pgvector
        # Similitud = 1 - Distancia
        query = """
            SELECT id, content, 1 - (embedding <=> %s) as similarity
            FROM documents
            ORDER BY embedding <=> %s
            LIMIT %s
        """
        
        # Convertir lista a string formato vector '[1,2,3]'
        embedding_str = str(query_embedding)
        
        # Ejecutar query
        results = execute_query(query, (embedding_str, embedding_str, limit), fetch_all=True)
        
        # Si results es None (error o vacio), devolver lista vacia
        if not results:
            return []

        app_logger.info(f"Found {len(results)} similar documents")
        return results

    except Exception as e:
        app_logger.error(f"Error searching similar documents: {str(e)}")
        raise