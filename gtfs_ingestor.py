import pandas as pd
import zipfile
import requests
import io
from sqlalchemy import create_engine
import os

# --- CONFIGURACIÓN CRÍTICA (SQLite) ---
# La base de datos ahora será un archivo local en la misma carpeta.
DATABASE_URL = "sqlite:///horarios.db" 
GTFS_STATIC_URL = "https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip"


def setup_database():
    """
    Descarga el GTFS, lo descomprime y carga los datos en la base de datos SQLite.
    """
    print("Iniciando ingesta de GTFS estático en SQLite...")
    
    # 1. CONEXIÓN A SQLite
    # Esto crea el archivo 'horarios.db' si no existe.
    engine = create_engine(DATABASE_URL) 
    
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
                    df = pd.read_csv(file, encoding='utf-8', low_memory=False)
                
                # Nombre de la tabla
                table_name = filename.replace('.txt', '')
                
                # Cargar el DataFrame en SQLite
                df.to_sql(table_name, engine, if_exists='replace', index=False)
                print(f"Tabla '{table_name}' cargada con {len(df)} registros.")

            else:
                print(f"ADVERTENCIA: Archivo {filename} no encontrado en el ZIP.")

        print("¡Ingesta de GTFS estático completada exitosamente!")
        
    except Exception as e:
        print(f"ERROR durante la ingesta: {e}")
        # Relanzamos el error para que el Cron Job lo detecte como fallo
        raise e

if __name__ == '__main__':
    setup_database()