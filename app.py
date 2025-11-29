from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)
# Permitir CORS para que tu frontend en localhost pueda acceder a la API
CORS(app)

# --- CONFIGURACIÓN CRÍTICA (SQLite) ---
# La API ahora consultará el archivo 'horarios.db' creado por el ingestor
DATABASE_URL = "sqlite:///horarios.db"
engine = create_engine(DATABASE_URL)

@app.route('/api/stations', methods=['GET'])
def get_stations():
    try:
        # Consulta SQL para obtener la ID y el nombre de todas las paradas
        # El nombre de la tabla es 'stops' (de stops.txt)
        query = text("SELECT stop_id, stop_name, stop_lat, stop_lon FROM stops ORDER BY stop_name;")
        
        with engine.connect() as connection:
            result = connection.execute(query).fetchall()
        
        stations = [
            {
                'stop_id': row[0],
                'name': row[1],
                'lat': row[2],
                'lon': row[3]
            }
            for row in result
        ]
        
        return jsonify(stations)
        
    except Exception as e:
        print(f"Error al consultar la base de datos: {e}")
        # Si la tabla aún no se ha creado (el ingestor no ha corrido), retornamos un error 500
        return jsonify({"error": "Error al cargar las estaciones", "details": str(e)}), 500

if __name__ == '__main__':
    # Usamos Gunicorn en producción, pero si lo ejecutas localmente:
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 8080))