import pandas as pd
import zipfile
import requests
import io
from sqlalchemy import create_engine
import os

# --- CONFIGURACIÓN CRÍTICA ---
# La variable de entorno DATABASE_URL es inyectada por el Workflow de GitHub Actions
# con el valor del secreto POSTGRES_URL.
DATABASE_URL = os.environ.get(
    "DATABASE_URL"
) 
GTFS_STATIC_URL = "https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip"

# RUTA AL CERTIFICADO SSL: Debe coincidir con el archivo que subiste a GitHub.
SSL_CERT_PATH = "supabase-cert.cert" 

# Verifica que la URL esté presente antes de intentar conectarse.
if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL no está configurada. Verifica el secreto de GitHub.")


def setup_database():
    """
    Descarga el GTFS, lo descomprime y carga los datos en la base de datos PostgreSQL.
    Añade la configuración SSL requerida por Supabase para forzar una conexión segura.
    """
    print("Iniciando ingesta de GTFS estático...")
    
    # 1. CONSTRUIR LA CADENA DE CONEXIÓN CON SSL
    # Usamos la sintaxis f-string para añadir el parámetro sslrootcert
    # Esto usa el certificado que subiste para verificar la conexión.
    connection_string = f"{DATABASE_URL}&sslrootcert={SSL_CERT_PATH}"
    
    # Reemplazamos 'postgresql' por 'postgresql+psycopg2' en la URL
    # Esto asegura que SQLAlchemy use el driver correcto.
    if connection_string.startswith("postgresql://"):
        connection_string = connection_string.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    engine = create_engine(connection_string)
    
    try:
        # 2. Descargar el archivo ZIP
        print(f"Descargando GTFS desde: {GTFS_STATIC_URL}")
        response = requests.get(GTFS_STATIC_URL)
        response.raise_for_status() 
        
        # 3. Leer el ZIP en memoria
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        
        # 4. Archivos clave a cargar
        REQUIRED_FILES = ['stops.txt', 'trips.txt', 'stop_times.txt', 'routes.txt']

        for filename in REQUIRED_FILES:
            if filename in zip_file.namelist():
                print(f"Cargando {filename}...")
                
                with zip_file.open(filename) as file:
                    # Lee el archivo .txt (CSV)
                    # Usamos 'low_memory=False' para manejar archivos potencialmente grandes
                    df = pd.read_csv(file, encoding='utf-8', low_memory=False)
                
                # Nombre de la tabla
                table_name = filename.replace('.txt', '')
                
                # Cargar el DataFrame en PostgreSQL
                # 'replace' borra la tabla existente y crea una nueva.
                df.to_sql(table_name, engine, if_exists='replace', index=False)
                print(f"Tabla '{table_name}' cargada con {len(df)} registros.")

            else:
                print(f"ADVERTENCIA: Archivo {filename} no encontrado en el ZIP.")

        print("¡Ingesta de GTFS estático completada exitosamente!")
        
    except Exception as e:
        # Usamos 'psycopg2' en la excepción para ser específicos en el error de conexión.
        print(f"ERROR: Falló la conexión/ingesta. Causa: {e}")
        # Relanzamos el error para que GitHub Actions marque la tarea como fallida
        raise e

if __name__ == '__main__':
    setup_database()