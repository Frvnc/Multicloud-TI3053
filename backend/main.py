import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

# cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuracion de urls MultiCloud (Cargadas desde el .env del servidor)
azure_url = os.getenv("AZURE_STORAGE_URL", "http://azure-mock-local")
aws_url = os.getenv("AWS_STORAGE_URL", "http://aws-mock-local")
CONTAINER_LAB = os.getenv("AZURE_CONTAINER_LAB", "laboratorio")

# Configuracion de Base de Datos
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#  modelos SQLalchemy
class Paciente(Base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True, index=True)
    rut = Column(String(20), unique=True, index=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    examenes = relationship("Examen", back_populates="paciente")

class Examen(Base):
    __tablename__ = "examenes"
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    tipo_examen = Column(String(20), nullable=False) # 'laboratorio' o 'imagenologia'
    nombre_archivo = Column(String(255), nullable=False)
    fecha_subida = Column(DateTime, default=datetime.now(timezone.utc))
    paciente = relationship("Paciente", back_populates="examenes")

# Configuracion fastapi
app = FastAPI(title="API Resultados HHHA - MultiCloud")

# Configuracion de CORS para permitir que el Frontend (puerto 80) hable con el Backend (puerto 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper para generar la URL de descarga segun la nube
def generar_url_multicloud(tipo: str, nombre_archivo: str) -> str:
    if tipo == "laboratorio":
        # logica Azure: URL_BASE/CONTENEDOR/ARCHIVO.pdf
        return f"{azure_url}/{CONTAINER_LAB}/{nombre_archivo}"
    else:
        # logica AWS S3: URL_BASE/ARCHIVO.jpg
        return f"{aws_url}/{nombre_archivo}"

# Endpoint Principal (Ajustado para coincidir con el fetch del Frontend)
@app.get("/paciente/{rut_paciente}")
def obtener_resultados(rut_paciente: str):
    db = SessionLocal()
    try:
        # Buscar paciente por RUT
        paciente = db.query(Paciente).filter(Paciente.rut == rut_paciente).first()
        
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
            
        resultados = []
        for examen in paciente.examenes:
            # Generar URL dinamica basada en el tipo de examen
            url_descarga = generar_url_multicloud(examen.tipo_examen, examen.nombre_archivo)
            
            resultados.append({
                "id": examen.id,
                "tipo_examen": examen.tipo_examen,
                "nombre_archivo": examen.nombre_archivo,
                "url_descarga": url_descarga
            })
            
        return {
            "paciente": {
                "rut": paciente.rut,
                "nombre": paciente.nombre,
                "email": paciente.email
            },
            "examenes": resultados
        }
    finally:
        db.close()