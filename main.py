from fastapi import FastAPI

#nueva instancia de fastapi
app = FastAPI()

@app.get('/')
def message():
    return "hola mundo"

#ejecutar con  uvicorn main:app --reload --port 5000 --host 0.0.0.0
