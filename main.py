from fastapi import FastAPI, Body
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
    """ 
    Get sin parametros a la ruta raiz.
    Devuelve un mensaje de bienvenida.
    """
    return HTMLResponse(content=
    "<h1>Hola mundo desde FastAPI</h1>",
    status_code=200)

@app.get('/contact', tags=['Contact']) 
def getAllContact():
    """ 
    Get sin parametros pero a la ruta /contact.
    Devuelve todos los contactos.
    """
    return (contactos)

@app.get('/contact/{id}', tags=['Contact']) 
def getContact(id: int):
    """ 
    Get con parametro de path.
    Devuelve un contacto por su ID.
    """
    for item in contactos:
        if item["id"] == id:
            return item
    return []

@app.get('/contact/', tags=['Contact'])  
def getContactByName(name: str):        
    """ 
    Get con parametro de query.
    La barra del final es para indicar que se va a recibir un parametro de tipo query
    Devuelve un contacto por su nombre.
    """
    for item in contactos:
        if item["nombre"] == name:
            return item
    return []

@app.post('/contact', tags=['Contact'])
def addContact(id: int = Body(), nombre: str = Body(), email: str = Body()):
    """ 
    Post con parametro de body (payload).
    Añade un contacto.
    """
    contact = {"id": id, "nombre": nombre, "email": email}  
    contactos.append(contact)
    return contactos

@app.put('/contact/{id}', tags=['Contact'])
def updateContact(id: int, nombre: str = Body(), email: str = Body()):
    """ 
    Put con parametro de path y body (payload).
    Actualiza un contacto por su ID.
    """
    for item in contactos:
        if item["id"] == id:
            item["nombre"] = nombre
            item["email"] = email
            return contactos


@app.delete('/contact/{id}', tags=['Contact'])
def deleteContact(id: int):
    """ 
    Delete con parametro de path.
    Elimina un contacto por su ID.
    """
    for item in contactos:
        if item["id"] == id:
            contactos.remove(item)
            return contactos
    
"""
ejecutar con  uvicorn main:app --reload --port 5000 --host 0.0.0.0
"""

