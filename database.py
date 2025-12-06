import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection string
DATABASE_URL = os.getenv("DATABASE_URL")

# Pool global
db_pool = None

def init_db_pool():
    global db_pool
    if db_pool is None:
        try:
            # Crear pool de conexiones
            db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=DATABASE_URL,
                cursor_factory=RealDictCursor
            )
            logger.info("✅ Pool de conexiones a base de datos inicializado.")
        except Exception as e:
            logger.error(f"❌ Error al inicializar pool de conexiones: {e}")
            raise e

@contextmanager
def get_db_connection():
    """
    Context manager para obtener una conexión del pool.
    Maneja commit/rollback y retorno al pool automáticamente.
    """
    global db_pool
    if db_pool is None:
        init_db_pool()
    
    conn = None
    try:
        conn = db_pool.getconn()
        yield conn
        conn.commit()
    except Exception as e:
        logger.error(f"Error en operación de base de datos: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            db_pool.putconn(conn)

def execute_query(query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
    """
    Helper para ejecutar queries simples
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            
            if fetch_one:
                return cur.fetchone()
            if fetch_all:
                return cur.fetchall()
            
            # Para inserts/updates que retornan datos, cur.fetchone() o fetchall() funciona si se usa RETURNING
            try:
                if cur.description: # Si hay resultados para leer
                     return cur.fetchall()
            except:
                pass
            return None