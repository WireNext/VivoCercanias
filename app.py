from flask import Flask, jsonify
from sqlalchemy import create_engine, text
from flask_cors import CORS
from datetime import datetime
import os

# --- CONFIGURACIÓN ---
# Usa la variable de entorno DATABASE_URL, o el valor por defecto
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://user:password@host:port/dbname" # ¡CAMBIA ESTO PARA PRUEBAS LOCALES!
) 
app = Flask(__name__)
# Habilita CORS para permitir que el JS del frontend acceda a esta API
CORS(app) 
engine = create_engine(DATABASE_URL)

# --- ENDPOINT 1: LISTAR ESTACIONES (Para dibujar el mapa) ---
@app.route('/api/stations', methods=['GET'])
def list_stations():
    """Devuelve la lista de estaciones (stops) para dibujar el mapa."""
    sql_query = text("SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops;")
    
    try:
        with engine.connect() as connection:
            stops = connection.execute(sql_query).fetchall()
            stations_list = [dict(row._mapping) for row in stops]
            return jsonify(stations_list)
    except Exception as e:
        app.logger.error(f"Error al listar estaciones: {e}")
        return jsonify({"error": "No se pudieron cargar las estaciones."}), 500

# --- ENDPOINT 2: HORARIOS PROGRAMADOS (Para la lógica del Frontend) ---
@app.route('/api/station/<stop_id>/scheduled', methods=['GET'])
def get_station_scheduled(stop_id):
    """
    Devuelve los horarios estáticos (programados) de los próximos trenes.
    """
    now = datetime.now()
    time_str = now.strftime('%H:%M:%S')
    
    # Consulta SQL para obtener los próximos 15 viajes programados después de la hora actual
    sql_query = text("""
        SELECT
            st.arrival_time,
            st.trip_id,
            t.trip_headsign,
            r.route_long_name
        FROM stop_times st
        JOIN trips t ON st.trip_id = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        WHERE st.stop_id = :stop_id
          AND st.arrival_time >= :current_time
        ORDER BY st.arrival_time
        LIMIT 15;
    """)
    
    results = []
    
    try:
        with engine.connect() as connection:
            db_rows = connection.execute(sql_query, {"stop_id": stop_id, "current_time": time_str}).fetchall()
            
            for row in db_rows:
                results.append({
                    "trip_id": row[1],
                    "destino": row[2],
                    "linea": row[3],
                    "programado": str(row[0]),
                    "stop_id": stop_id 
                })

        return jsonify(results)

    except Exception as e:
        app.logger.error(f"Error en la consulta de la API: {e}")
        return jsonify({"error": "No se pudieron obtener los datos programados."}), 500

if __name__ == '__main__':
    # Usar puerto 8080 en entornos cloud como Cloud Run
    app.run(debug=True, host='0.0.0.0', port=8080)