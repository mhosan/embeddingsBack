# config.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client, ClientOptions

# Cargar variables de entorno
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print(f"ERROR CONFIG: Missing Supabase Env Vars -> URL: {bool(supabase_url)}, KEY: {bool(supabase_key)}")

# Crear cliente desactivando la persistencia de sesión local para evitar errores de bloqueo de archivos en Vercel Serverless
supabase: Client = create_client(
    supabase_url or "",
    supabase_key or "",
    options=ClientOptions(
        persist_session=False
    )
)

print(f"Conexion iniciada a Supabase (URL: {supabase_url[:15] if supabase_url else 'None'}...)")