import os
from dotenv import load_dotenv
from database import get_connection

load_dotenv()

# Probar conexion a Neon
try:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM documents;")
        row = cur.fetchone()
        print(f"[OK] Conexion a Neon exitosa. Total de documentos: {row['total']}")
    conn.close()
except Exception as e:
    print(f"[ERROR] al conectar a Neon: {e}")