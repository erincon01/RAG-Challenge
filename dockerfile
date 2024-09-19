# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala las dependencias del sistema necesarias para psycopg2 y otras compilaciones
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo requirements.txt desde el directorio python
COPY ./python/requirements.txt /app/requirements.txt

RUN cat /app/requirements.txt

# Instala las dependencias desde requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia todos los archivos Python al contenedor
COPY ./python/*.py /app/

# Copia los archivos del directorio raíz (./) al contenedor
COPY ./*.py /app/

# Copia los archivos .md, .pdf y .mp4 del directorio raíz, sin incluir subdirectorios
COPY ./*.md /app/
COPY ./*.pdf /app/
COPY ./*.mp4 /app/

# Copia el directorio data completo
COPY ./data/scripts_summary /app/data/scripts_summary
COPY ./images /app/images

# Expone el puerto 8501, que es el puerto por defecto de Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación Streamlit
CMD ["streamlit", "run", "main_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
