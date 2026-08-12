# config.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client, ClientOptions

# Cargar variables de entorno
load_dotenv()

# Crear cliente desactivando la persistencia de sesión local para evitar errores de bloqueo de archivos en Vercel Serverless
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
    options=ClientOptions(
        persist_session=False
    )
)

print("Conexion exitosa a Supabase")