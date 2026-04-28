FROM python:3.13-slim

WORKDIR /app

# Instalar dependencias primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto de la API
EXPOSE 8000

# Comando para iniciar el servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]