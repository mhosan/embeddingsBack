from sqlalchemy import text
from database import SessionLocal

def test_db_connection():
    print("Intentando conectar a la base de datos...")
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        print("¡Conexión a la base de datos exitosa!")
        print("Resultado de 'SELECT 1':", result.fetchone())
    except Exception as e:
        print("Error al conectar a la base de datos:", e)
    finally:
        if 'db' in locals() and db:
            db.close()
            print("Conexión cerrada.")

if __name__ == "__main__":
    test_db_connection() 