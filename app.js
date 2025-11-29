// --- 1. CONFIGURACIÓN ---
// ¡IMPORTANTE! Reemplaza esto con la URL de tu servidor Flask desplegado
const API_BASE_URL = "http://localhost:8080"; 
const GTFS_RT_URL = "https://gtfsrt.renfe.com/trip_updates.pb";
const REFRESH_INTERVAL_MS = 30000; // Refrescar datos cada 30 segundos

let currentStopId = null; // ID de la estación seleccionada actualmente
let lastUpdate = 'N/A';

// Inicializa el mapa (Leaflet)
const map = L.map('map').setView([40.4168, -3.7038], 6); // Madrid, nivel 6 de zoom

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// --- 2. LÓGICA DE PARSING DE PROTOBUF (CRÍTICO) ---
// **ESTA FUNCIÓN REQUIERE UNA LIBRERÍA JS PARA LEER PROTOBUF Y EL ESQUEMA GTFS-RT**
// Como no podemos incluir una librería completa aquí, simularemos el resultado.
// En la vida real, usarías protobufjs (o similar) para leer el buffer binario.

async function fetchRealtimeUpdates() {
    try {
        const response = await fetch(GTFS_RT_URL);
        const buffer = await response.arrayBuffer();
        
        // --- INICIO DE LA SIMULACIÓN DE PARSING ---
        // En un proyecto real, se usaría un parser JS para convertir 'buffer' a un objeto JSON.
        // Aquí simulamos el output esperado: {trip_id: {stop_id: estimated_time_string, ...}}
        
        // Dado que esto es complejo, te daré un ejemplo de cómo se vería la estructura de datos:
        
        // Simulación de la caché RT (Solo para que el código compile y la lógica funcione)
        const mock_rt_cache = {
             // Ejemplo de trip_id y su actualización en stop_id '35307'
             "5477_00030_03": {"35307": "13:45:00", "35407": "14:15:00"} 
        };
        lastUpdate = new Date().toLocaleTimeString();
        return mock_rt_cache;
        // --- FIN DE LA SIMULACIÓN DE PARSING ---

    } catch (error) {
        console.error("Error al obtener o parsear el feed Realtime:", error);
        return {};
    }
}


// --- 3. CARGA DE ESTACIONES Y MANEJADOR DE CLICKS ---

async function loadStations() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stations`);
        const stations = await response.json();

        stations.forEach(station => {
            const marker = L.marker([station.stop_lat, station.stop_lon]).addTo(map);
            marker.bindPopup(`<b>${station.stop_name}</b>`);
            marker.on('click', () => {
                displayRealtimeData(station.stop_id, station.stop_name);
            });
        });

    } catch (error) {
        console.error("Error al cargar las estaciones:", error);
        document.getElementById('station-title').innerText = "Error al conectar con la API de Backend.";
    }
}

// --- 4. FUNCIÓN DE VISUALIZACIÓN Y MATCHING ---

async function displayRealtimeData(stopId, stationName) {
    currentStopId = stopId;
    document.getElementById('realtime-data').innerHTML = '<p>Cargando información en tiempo real...</p>';
    document.getElementById('station-title').innerHTML = `Estación: <b>${stationName}</b>`;

    const update = async () => {
        if (!currentStopId) return;

        // 1. Obtener Horarios Programados (desde tu servidor Python)
        const scheduledResponse = await fetch(`${API_BASE_URL}/api/station/${currentStopId}/scheduled`);
        const scheduledTrains = await scheduledResponse.json();

        // 2. Obtener Actualizaciones RT (directamente desde Renfe .pb)
        const rtUpdates = await fetchRealtimeUpdates(); 

        const combinedData = scheduledTrains.map(train => {
            const rtTripUpdate = rtUpdates[train.trip_id];
            
            let estimatedTime = train.programado;
            let status = "Programado";
            let statusClass = "status-prog";

            if (rtTripUpdate && rtTripUpdate[train.stop_id]) {
                estimatedTime = rtTripUpdate[train.stop_id];
                status = "En tiempo real";
                statusClass = "status-rt";
            }
            // (Lógica para CANCELADO iría aquí si el feed RT lo indica)

            return {
                ...train,
                estimado: estimatedTime,
                estado: status,
                statusClass: statusClass
            };
        });

        // 3. Renderizar la Información
        renderData(combinedData, stationName);
    };

    // 4. Ejecutar inmediatamente y configurar el refresh
    update();
    clearInterval(window.refreshTimer); 
    window.refreshTimer = setInterval(update, REFRESH_INTERVAL_MS);
}

function renderData(data, stationName) {
    const dataContainer = document.getElementById('realtime-data');
    dataContainer.innerHTML = '';

    if (data.length === 0) {
        dataContainer.innerHTML = '<p>No hay próximos trenes en el horario disponible.</p>';
        return;
    }

    data.forEach(train => {
        const html = `
            <div class="train-info">
                <strong>Destino:</strong> ${train.destino} (${train.linea})<br>
                <strong>Programado:</strong> ${train.programado}<br>
                <strong>Estimado:</strong> <span class="${train.statusClass}">${train.estimado}</span><br>
                <strong>Estado:</strong> <span class="${train.statusClass}">${train.estado}</span>
            </div>
        `;
        dataContainer.innerHTML += html;
    });

    dataContainer.innerHTML += `<p style="font-size: 0.8em; margin-top: 10px;">Última actualización de datos RT: ${lastUpdate}</p>`;
}

// Iniciar la aplicación cargando las estaciones
document.addEventListener('DOMContentLoaded', loadStations);