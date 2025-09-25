from fastapi import FastAPI
from fastapi.responses import HTMLResponse


app = FastAPI()
app.title = "Mi app con FastAPI"
app.version = "0.0.1"

contactos = [
    {"id": 1, "nombre": "Juan", "email": "juan@example.com"},
    {"id": 2, "nombre": "María", "email": "maria@example.com"},
    {"id": 3, "nombre": "Pedro", "email": "pedro@example.com"},
    {"id": 4, "nombre": "Ana", "email": "ana@example.com"},
    {"id": 5, "nombre": "Luis", "email": "luis@example.com"},
    {"id": 6, "nombre": "Laura", "email": "laura@example.com"},
    {"id": 7, "nombre": "Carlos", "email": "carlos@example.com"},
    {"id": 8, "nombre": "Sofía", "email": "sofia@example.com"},
]

@app.get('/', tags=['Home'])
def message():
    return HTMLResponse(content=
    "<h1>Hola mundo desde FastAPI</h1>",
    status_code=200)

@app.get('/contact', tags=['Contact']) #<-- sin parametros
def getAllContact():
    return (contactos)

@app.get('/contact/{id}', tags=['Contact']) #<-- parametro de tipo path
def getContact(id: int):
    for item in contactos:
        if item["id"] == id:
            return item
    return []

@app.get('/contact/', tags=['Contact']) #<-- parametro de tipo query. La barra del final es para indicar que se va a 
def getContactByName(name: str):        # recibir un parametro de tipo query
    for item in contactos:
        if item["nombre"] == name:
            return item
    return []



#ejecutar con  uvicorn main:app --reload --port 5000 --host 0.0.0.0
