import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def _sanitize_neon_url(url: str) -> str:
    """
    Limpia la URL de conexion de Neon para compatibilidad con psycopg2:
    - Elimina channel_binding (no soportado por psycopg2 < 2.9.5 / libpq antiguo)
    - Asegura sslmode=require
    """
    if not url:
        return url

    # Quitar channel_binding
    url = re.sub(r'[&?]channel_binding=[^&]*', '', url)

    # Asegurar sslmode=require
    if "sslmode" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require"

    return url

def get_connection():
    """
    Crea y retorna una nueva conexion a la base de datos Neon (PostgreSQL).
    Cada llamada genera una conexion fresca para evitar problemas de sockets
    congelados en entornos serverless (Vercel, AlwaysData, etc.).
    """
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        raise RuntimeError("ERROR CONFIG: La variable de entorno DATABASE_URL no esta definida.")

    database_url = _sanitize_neon_url(raw_url)

    conn = psycopg2.connect(
        database_url,
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=10
    )
    return conn

print("Neon DB: modulo de conexion inicializado correctamente")