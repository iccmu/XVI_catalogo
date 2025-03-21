from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import sys

app = FastAPI(title="API Teatro Histórico")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar directorio static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Modelos Pydantic
class Detalles(BaseModel):
    lugar: Optional[str] = None
    edicion: Optional[str] = None
    editor: Optional[str] = None
    publicacion: Optional[str] = None
    imprenta: Optional[str] = None
    formato: Optional[str] = None
    referencias: Optional[List[str]] = None
    personajes: Optional[List[str]] = None
    tema: Optional[str] = None
    notas: Optional[str] = None
    # Otros campos opcionales que puedan aparecer en detalles

class Subobra(BaseModel):
    id: str
    titulo: str
    personajes: Optional[List[str]] = None
    autor: Optional[str] = None
    detalles: Optional[Dict[str, Any]] = None

class Obra(BaseModel):
    id: int
    titulo: str
    autor: str
    fecha: str
    personajes: Optional[List[str]] = None
    detalles: Optional[Dict[str, Any]] = None
    subobras: Optional[List[Subobra]] = None

class Periodo(BaseModel):
    periodo: str
    obras: List[Obra]

# Obtener la ruta base cuando se ejecuta como ejecutable
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(base_path, "DATA/ALL_COMBINED_RESP")
periodos = {}

def load_data():
    print(f"Intentando cargar datos desde: {os.path.abspath(DATA_DIR)}")
    try:
        if not os.path.exists(DATA_DIR):
            print(f"ERROR: El directorio {DATA_DIR} no existe!")
            return
        
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(DATA_DIR, filename)
                print(f"Cargando archivo: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        periodos[data['periodo']] = data
                        print(f"Archivo {filename} cargado correctamente")
                except Exception as e:
                    print(f"Error al cargar {filename}: {str(e)}")
        
        print(f"Total de períodos cargados: {len(periodos)}")
        print(f"Períodos disponibles: {list(periodos.keys())}")
    except Exception as e:
        print(f"Error general al cargar datos: {str(e)}")

# Cargar datos al inicio
load_data()

# Rutas API
@app.get("/")
async def root():
    print("Acceso a la ruta raíz (/)")
    return FileResponse('SCRIPTS/index.html')

@app.get("/periodos")
async def get_periodos():
    print(f"Acceso a /periodos - Períodos disponibles: {list(periodos.keys())}")
    return {"periodos": list(periodos.keys())}

@app.get("/periodo/{periodo_id}")
async def get_periodo(periodo_id: str):
    if periodo_id not in periodos:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
    return periodos[periodo_id]

@app.get("/obras")
async def get_todas_obras():
    todas_obras = []
    for periodo in periodos.values():
        todas_obras.extend(periodo['obras'])
    return {"obras": todas_obras}

@app.get("/obra/{obra_id}")
async def get_obra(obra_id: int):
    for periodo in periodos.values():
        for obra in periodo['obras']:
            if obra['id'] == obra_id:
                return obra
    raise HTTPException(status_code=404, detail="Obra no encontrada")

@app.get("/buscar")
async def buscar_obras(
    titulo: Optional[str] = None,
    autor: Optional[str] = None,
    fecha: Optional[str] = None
):
    resultados = []
    for periodo in periodos.values():
        for obra in periodo['obras']:
            if (titulo is None or titulo.lower() in obra['titulo'].lower()) and \
               (autor is None or autor.lower() in obra['autor'].lower()) and \
               (fecha is None or fecha in obra['fecha']):
                resultados.append(obra)
    return {"resultados": resultados}

# Añadir endpoint para favicon
@app.get('/favicon.ico')
async def favicon():
    return FileResponse('static/favicon.ico')

if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
