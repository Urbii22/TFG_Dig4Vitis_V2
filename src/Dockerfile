# Utilizar una imagen base oficial de Python
FROM python:3.11.5

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de requisitos
COPY requirements.txt .

# Instalar las dependencias del archivo de requisitos
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos de la aplicación en el contenedor
COPY . .

# Exponer el puerto que utilizará Streamlit
EXPOSE 8502

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "main.py"]