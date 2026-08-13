import os
from dotenv import load_dotenv
from supabase import create_client, Client, ClientOptions

# Cargar variables de entorno
load_dotenv()

class SupabaseProxy:
    """
    Proxy dinamico para crear una instancia nueva de Supabase Client en cada llamada.
    Esto evita el error '[Errno 16] Device or resource busy' causado por el cliente HTTP (httpx)
    reutilizando sockets congelados/bloqueados en el entorno Serverless de Vercel.
    """
    @staticmethod
    def _get_client() -> Client:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            print(f"ERROR CONFIG: Missing Supabase Env Vars -> URL: {bool(supabase_url)}, KEY: {bool(supabase_key)}")
        return create_client(
            supabase_url or "",
            supabase_key or "",
            options=ClientOptions(
                persist_session=False
            )
        )

    def __getattr__(self, name):
        client = self._get_client()
        return getattr(client, name)

# Instancia global exportada del Proxy
supabase = SupabaseProxy()

print("Supabase Dynamic Proxy inicializado correctamente")