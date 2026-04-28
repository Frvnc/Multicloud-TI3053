import os
import re
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from dotenv import load_dotenv

# cargar variables de entorno
load_dotenv()

# configuracion multicloud
azure_url = os.getenv("AZURE_STORAGE_URL", "http://azure-mock-local")
aws_url = os.getenv("AWS_STORAGE_URL", "http://aws-mock-local")
container_lab = os.getenv("AZURE_CONTAINER_LAB", "laboratorio")

# configuracion de base de datos
database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)
sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
base = declarative_base()

# modelos de la base de datos
class Paciente(base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True, index=True)
    rut = Column(String(20), unique=True, index=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    examenes = relationship("Examen", back_populates="paciente")

class Examen(base):
    __tablename__ = "examenes"
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    tipo_examen = Column(String(20), nullable=False) 
    nombre_archivo = Column(String(255), nullable=False)
    fecha_subida = Column(DateTime, default=datetime.now(timezone.utc))
    paciente = relationship("Paciente", back_populates="examenes")

app = FastAPI(title="api resultados hhha - multicloud")

# configuracion de cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# dependencia para la sesion de db
def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()

# funcion para limpiar el rut quita puntos guiones y espacios
def limpiar_y_validar_rut(rut: str):
    limpio = re.sub(r'[^0-9kK]', '', rut).lower()
    if len(limpio) < 8 or len(limpio) > 9:
        raise HTTPException(
            status_code=400, 
            detail="formato de rut invalido ingrese entre 8 y 9 caracteres"
        )
    return limpio

# genera la url segun el proveedor de nube
def generar_url_multicloud(tipo: str, nombre_archivo: str) -> str:
    if tipo.lower() == "laboratorio":
        return f"{azure_url}/{container_lab}/{nombre_archivo}"
    else:
        return f"{aws_url}/{nombre_archivo}"

# endpoint unificado para obtener paciente y sus examenes
@app.get("/paciente/{rut}")
async def obtener_datos_completos(rut: str, db: Session = Depends(get_db)):
    # limpieza del rut antes de la consulta
    rut_formateado = limpiar_y_validar_rut(rut)
    
    # busqueda en base de datos
    paciente = db.query(Paciente).filter(Paciente.rut == rut_formateado).first()
    
    if not paciente:
        raise HTTPException(
            status_code=404, 
            detail=f"no se encontro informacion para el rut {rut}"
        )
    
    # construir lista de examenes con urls dinamicas
    resultados = []
    for examen in paciente.examenes:
        url_descarga = generar_url_multicloud(examen.tipo_examen, examen.nombre_archivo)
        resultados.append({
            "id": examen.id,
            "tipo_examen": examen.tipo_examen,
            "nombre_archivo": examen.nombre_archivo,
            "url_descarga": url_descarga
        })
    
    # respuesta estructurada para el frontend
    return {
        "paciente": {
            "rut": paciente.rut,
            "nombre": paciente.nombre,
            "email": paciente.email
        },
        "examenes": resultados
    }