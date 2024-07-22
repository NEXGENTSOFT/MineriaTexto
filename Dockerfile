# Usa una imagen base oficial de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo requirements.txt y el código de la aplicación en el contenedor
COPY requirements.txt requirements.txt
COPY app.py app.py

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto en el que correrá la aplicación
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]
