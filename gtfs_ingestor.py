import pandas as pd
import zipfile
import requests
import io
from sqlalchemy import create_engine
import os

# --- CONFIGURACIÓN ---
# Usamos una variable de entorno para la URL de la base de datos
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://user:password@host:port/dbname" # ¡CAMBIA ESTO PARA PRUEBAS LOCALES!
) 
GTFS_STATIC_URL = "https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip"

def setup_database():
    """Descarga el GTFS, lo descomprime y carga los datos en la base de datos."""
    print("Iniciando ingesta de GTFS estático...")
    engine = create_engine(DATABASE_URL)
    
    try:
        # 1. Descargar el archivo ZIP
        print(f"Descargando GTFS desde: {GTFS_STATIC_URL}")
        response = requests.get(GTFS_STATIC_URL)
        response.raise_for_status() 
        
        # 2. Leer el ZIP en memoria
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        
        # 3. Archivos clave a cargar
        REQUIRED_FILES = ['stops.txt', 'trips.txt', 'stop_times.txt', 'routes.txt']

        for filename in REQUIRED_FILES:
            if filename in zip_file.namelist():
                print(f"Cargando {filename}...")
                
                with zip_file.open(filename) as file:
                    # Lee el archivo .txt (CSV)
                    df = pd.read_csv(file, encoding='utf-8')
                
                # Nombre de la tabla
                table_name = filename.replace('.txt', '')
                
                # Cargar el DataFrame en PostgreSQL
                # 'replace' borra la tabla existente y crea una nueva.
                df.to_sql(table_name, engine, if_exists='replace', index=False)
                print(f"Tabla '{table_name}' cargada con {len(df)} registros.")

            else:
                print(f"ADVERTENCIA: Archivo {filename} no encontrado en el ZIP.")

        print("¡Ingesta de GTFS estático completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"ERROR durante la ingesta: {e}")
        return False

if __name__ == '__main__':
    setup_database()