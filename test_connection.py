from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Conectar
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Probar con una consulta simple
try:
    response = supabase.table('documents').select("*").limit(1).execute()
    print("✅ Conexión exitosa")
    print(f"Datos obtenidos: {response.data}")
except Exception as e:
    print(f"❌ Error: {e}")