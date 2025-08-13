# Utilizar una imagen base oficial de Python
FROM python:3.11.5-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

## Copiar el archivo de requisitos
COPY src/requirements.txt ./requirements.txt

# Instalar las dependencias del archivo de requisitos
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos de la aplicación en el contenedor
COPY . .

# Create non-root user
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Exponer el puerto que utilizará Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import socket; s=socket.socket(); s.settimeout(3); s.connect(('127.0.0.1',8501)); print('ok')"

CMD ["streamlit", "run", "src/main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.maxUploadSize=2000"]
