import logging
from typing import List, Dict, Any
from database import get_connection

app_logger = logging.getLogger(__name__)

def search_similar_documents(query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """ ==========================================================================================
    Busca documentos similares en la tabla 'documents' usando similitud coseno (pgvector).
    Args:
        query_embedding: Vector de embedding para la consulta (lista de floats).
        limit: Número máximo de resultados a retornar (default 5).
    Returns:
        Lista de diccionarios con 'id', 'content', 'similarity' (similitud coseno).
        Usa el operador <=> de pgvector directamente sobre la columna 'embedding'.
    =========================================================================================== """
    try:
        app_logger.info(f"Buscando documentos similares. Dimensiones del embedding: {len(query_embedding)}, limit: {limit}")

        # Convertir el vector a formato string de pgvector: '[0.1, 0.2, ...]'
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        sql = """
            SELECT
                id,
                content,
                1 - (embedding <=> %s::vector) AS similarity
            FROM documents
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (embedding_str, embedding_str, limit))
                rows = cur.fetchall()
        finally:
            conn.close()

        results = [
            {
                'id': row['id'],
                'content': row['content'],
                'similarity': float(row['similarity'])
            }
            for row in rows
        ]

        app_logger.info(f"Documentos similares encontrados: {len(results)}")
        return results

    except Exception as e:
        app_logger.error(f"Error buscando documentos similares: {str(e)}")
        raise