import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Configuración de URLs MultiCloud (Nube A y Nube B)
azure_url = os.getenv("AZURE_STORAGE_URL", "http://azure-mock-local")
aws_url = os.getenv("AWS_STORAGE_URL", "http://aws-mock-local")

# 1. Configuración de Base de Datos
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Modelos SQLAlchemy
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

# 3. Configuración de Contenedores/Buckets
# Azure usa subcarpetas (laboratorio), AWS suele usar la raíz del bucket
CONTAINER_LAB = os.getenv("AZURE_CONTAINER_LAB", "laboratorio")

# 4. Configuración FastAPI
app = FastAPI(title="API Resultados HHHA - MultiCloud (Azure & AWS)")

# Permitir peticiones desde el frontend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Helper para generar la URL de descarga según la nube
def generar_url_multicloud(tipo: str, nombre_archivo: str) -> str:
    if tipo == "laboratorio":
        # Lógica para Azure: URL/contenedor/archivo
        return f"{azure_url}/{CONTAINER_LAB}/{nombre_archivo}"
    else:
        # Lógica para AWS S3: URL/archivo (asumiendo que están en la raíz del bucket)
        return f"{aws_url}/{nombre_archivo}"

# 6. Endpoint Principal
@app.get("/api/resultados/{rut_paciente}")
def obtener_resultados(rut_paciente: str):
    db = SessionLocal()
    try:
        paciente = db.query(Paciente).filter(Paciente.rut == rut_paciente).first()
        
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
            
        resultados = []
        for examen in paciente.examenes:
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