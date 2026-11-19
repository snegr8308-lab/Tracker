from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import time
import socket
import threading

# Импортируем определение моделей из файла phones.py
from phones import get_phone_name

app = FastAPI()
devices = {}

# Фоновый UDP-сервер для локального поиска в Wi-Fi
def udp_discovery_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', 8011))
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data.decode('utf-8') == "DISCOVER_TRACKER_SERVER":
                sock.sendto(b"TRACKER_SERVER_HERE:8010", addr)
        except Exception:
            pass

threading.Thread(target=udp_discovery_listener, daemon=True).start()

@app.post("/api/data")
async def receive_data(request: Request):
    data = await request.json()
    raw_device_id = data.get("device_id", "Неизвестное устройство")
    
    # Получаем название из базы phones.py
    pretty_name = get_phone_name(raw_device_id)

    devices[pretty_name] = {
        "raw_id": raw_device_id,
        "lat": data.get("lat", 0.0),
        "lng": data.get("lng", 0.0),
        "battery": data.get("battery", 0),
        "charging": data.get("charging", False),
        "wifi": data.get("wifi", "Неизвестно"),
        "last_seen": time.strftime("%H:%M:%S")
    }
    return {"status": "ok"}

@app.get("/api/devices")
async def get_devices():
    return devices

@app.get("/", response_class=HTMLResponse)
async def get_map():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <title>Cyber Radar Tracker</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        
        <style>
            :root {
                --bg-main: #0a0d14;
                --panel-bg: rgba(16, 23, 38, 0.92);
                --card-bg: rgba(23, 32, 54, 0.8);
                --accent-green: #00ff9d;
                --accent-red: #ff2a6d;
                --accent-cyan: #00e5ff;
                --text-main: #e2e8f0;
                --text-muted: #94a3b8;
                --border-neon: rgba(0, 255, 157, 0.25);
            }

            * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
            body { font-family: 'Inter', sans-serif; background: var(--bg-main); color: var(--text-main); height: 100vh; overflow: hidden; display: flex; flex-direction: column; }

            #map { flex: 1; min-height: 48vh; z-index: 1; filter: saturate(1.2) contrast(1.1); }

            .top-control-bar {
                position: absolute;
                top: 12px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 1000;
                width: 92%;
                max-width: 500px;
                background: var(--panel-bg);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid var(--border-neon);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
                border-radius: 16px;
                padding: 10px 14px;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .control-title {
                font-family: 'Orbitron', sans-serif;
                font-size: 11px;
                letter-spacing: 1px;
                color: var(--accent-cyan);
                text-transform: uppercase;
                white-space: nowrap;
            }

            select {
                flex: 1;
                background: rgba(10, 15, 26, 0.85);
                color: var(--accent-green);
                font-family: 'Orbitron', sans-serif;
                font-size: 13px;
                padding: 8px 12px;
                border: 1px solid rgba(0, 229, 255, 0.35);
                border-radius: 10px;
                outline: none;
                cursor: pointer;
            }

            .sound-btn {
                background: rgba(0, 255, 157, 0.12);
                border: 1px solid var(--accent-green);
                color: var(--accent-green);
                padding: 8px 12px;
                border-radius: 10px;
                font-size: 14px;
                cursor: pointer;
            }
            .sound-btn.muted {
                border-color: var(--accent-red);
                color: var(--accent-red);
                background: rgba(255, 42, 109, 0.12);
            }

            #info-panel {
                height: 40vh;
                background: var(--panel-bg);
                backdrop-filter: blur(16px);
                border-top: 1px solid var(--border-neon);
                padding: 14px;
                overflow-y: auto;
            }

            .panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }
            .panel-header h3 {
                font-family: 'Orbitron', sans-serif;
                font-size: 13px;
                letter-spacing: 1.5px;
                color: var(--text-muted);
                text-transform: uppercase;
            }

            .card {
                background: var(--card-bg);
                border-radius: 14px;
                padding: 12px 14px;
                margin-bottom: 10px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-left: 4px solid var(--accent-green);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            }
            .card.out-of-range {
                border-left-color: var(--accent-red);
                opacity: 0.7;
            }

            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            .device-name {
                font-family: 'Orbitron', sans-serif;
                font-size: 14px;
                font-weight: 700;
                color: #fff;
            }
            .badge {
                font-size: 10px;
                font-weight: 700;
                padding: 3px 8px;
                border-radius: 20px;
                text-transform: uppercase;
            }
            .badge-green { background: rgba(0, 255, 157, 0.15); color: var(--accent-green); border: 1px solid var(--accent-green); }
            .badge-red { background: rgba(255, 42, 109, 0.15); color: var(--accent-red); border: 1px solid var(--accent-red); }

            .card-details {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 6px;
                font-size: 12px;
                color: var(--text-muted);
            }
            .detail-item span { color: #fff; font-weight: 600; }

            @keyframes pulse-ring {
                0% { transform: scale(0.5); opacity: 0.8; }
                100% { transform: scale(2.2); opacity: 0; }
            }

            .pulse-icon {
                position: relative;
                width: 16px;
                height: 16px;
                background: var(--accent-green);
                border-radius: 50%;
                border: 2px solid #fff;
                box-shadow: 0 0 10px var(--accent-green);
            }
            .pulse-icon::after {
                content: '';
                position: absolute;
                top: -6px; left: -6px; right: -6px; bottom: -6px;
                border: 2px solid var(--accent-green);
                border-radius: 50%;
                animation: pulse-ring 1.8s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
            }

            .leaflet-tile { filter: brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.3) brightness(0.7); }
            .leaflet-control-zoom { border: none !important; margin-top: 70px !important; }
            .leaflet-control-zoom a { background: var(--panel-bg) !important; color: var(--accent-cyan) !important; border-color: var(--border-neon) !important; }
        </style>
    </head>
    <body>

        <div class="top-control-bar">
            <span class="control-title">ЦЕНТР ЗОНЫ</span>
            <select id="myDeviceSelect" onchange="onDeviceSelectChange()"></select>
            <button id="soundBtn" class="sound-btn" onclick="toggleSound()">🔊</button>
        </div>

        <div id="map"></div>

        <div id="info-panel">
            <div class="panel-header">
                <h3>Active:</h3>
                <span id="target-count" class="badge badge-green">0 </span>
            </div>
            <div id="list">
                <div class="card out-of-range">
                    <div class="device-name">Поиск сигналов...</div>
                    <div class="card-details" style="margin-top:6px;">Ожидание GPS данных от устройств</div>
                </div>
            </div>
        </div>

        <script>
            var map = L.map('map', { zoomControl: true }).setView([50.45, 30.52], 14);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

            var markers = {};
            var radarCircle = null;
            var soundEnabled = true;
            var knownDevices = new Set();
            var audioCtx = new (window.AudioContext || window.webkitAudioContext)();

            function playSound(freq, duration, type = 'sine') {
                if (!soundEnabled) return;
                try {
                    if (audioCtx.state === 'suspended') audioCtx.resume();
                    var osc = audioCtx.createOscillator();
                    var gain = audioCtx.createGain();
                    osc.type = type;
                    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
                    gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
                    osc.connect(gain);
                    gain.connect(audioCtx.destination);
                    osc.start();
                    osc.stop(audioCtx.currentTime + duration);
                } catch(e) {}
            }

            function playRadarPing() { playSound(1200, 0.15, 'sine'); }
            function playNewTargetSound() {
                playSound(800, 0.1, 'triangle');
                setTimeout(() => playSound(1400, 0.2, 'triangle'), 100);
            }

            function toggleSound() {
                soundEnabled = !soundEnabled;
                var btn = document.getElementById('soundBtn');
                btn.innerText = soundEnabled ? '🔊' : '🔇';
                btn.classList.toggle('muted', !soundEnabled);
                if (soundEnabled) playRadarPing();
            }

            function createPulseIcon() {
                return L.divIcon({
                    className: 'custom-pulse-marker',
                    html: '<div class="pulse-icon"></div>',
                    iconSize: [16, 16],
                    iconAnchor: [8, 8]
                });
            }

            function onDeviceSelectChange() {
                playRadarPing();
                updateMap();
            }

            async function updateMap() {
                try {
                    let res = await fetch('/api/devices', {
                        headers: { 'ngrok-skip-browser-warning': 'true' }
                    });
                    let data = await res.json();

                    let select = document.getElementById('myDeviceSelect');
                    let selectedMyDevice = select.value;

                    for (let id in data) {
                        if (!Array.from(select.options).some(op => op.value === id)) {
                            let opt = document.createElement('option');
                            opt.value = id;
                            opt.innerHTML = id;
                            select.appendChild(opt);
                        }

                        if (!knownDevices.has(id)) {
                            knownDevices.add(id);
                            playNewTargetSound();
                        }
                    }

                    if (!selectedMyDevice && select.options.length > 0) {
                        selectedMyDevice = select.options[0].value;
                        select.value = selectedMyDevice;
                    }

                    let myCoords = null;
                    if (selectedMyDevice && data[selectedMyDevice]) {
                        myCoords = L.latLng(data[selectedMyDevice].lat, data[selectedMyDevice].lng);
                    }

                    if (myCoords && myCoords.lat !== 0) {
                        if (!radarCircle) {
                            radarCircle = L.circle(myCoords, {
                                color: '#00ff9d',
                                fillColor: '#00ff9d',
                                fillOpacity: 0.08,
                                weight: 1.5,
                                dashArray: '6, 6',
                                radius: 250
                            }).addTo(map);
                            map.setView(myCoords, 14);
                        } else {
                            radarCircle.setLatLng(myCoords);
                        }
                    }

                    let html = '';
                    let activeCount = 0;

                    for (let id in data) {
                        let d = data[id];
                        if (d.lat === 0 && d.lng === 0) continue;

                        activeCount++;
                        let targetCoords = L.latLng(d.lat, d.lng);
                        let distanceMeters = myCoords ? myCoords.distanceTo(targetCoords) : 0;
                        let distanceKm = (distanceMeters / 1000).toFixed(2);
                        let isWithin2Km = distanceMeters <= 2000;

                        if (isWithin2Km || id === selectedMyDevice) {
                            if (!markers[id]) {
                                markers[id] = L.marker(targetCoords, { icon: createPulseIcon() })
                                    .addTo(map)
                                    .bindPopup(`<b>${id}</b><br>Заряд: ${d.battery}%`);
                            } else {
                                markers[id].setLatLng(targetCoords);
                            }
                        } else {
                            if (markers[id]) {
                                map.removeLayer(markers[id]);
                                delete markers[id];
                            }
                        }

                        let statusClass = isWithin2Km ? 'card' : 'card out-of-range';
                        let badgeClass = isWithin2Km ? 'badge-green' : 'badge-red';
                        let rangeText = id === selectedMyDevice ? 'ЦЕНТР' : (isWithin2Km ? `${distanceKm} КМ` : `ВНЕ ЗОНЫ (${distanceKm} КМ)`);

                        html += `
                        <div class="${statusClass}">
                            <div class="card-header">
                                <span class="device-name">${id}</span>
                                <span class="badge ${badgeClass}">${rangeText}</span>
                            </div>
                            <div class="card-details">
                                <div class="detail-item">Заряд: <span>${d.battery}% ${d.charging ? '⚡' : ''}</span></div>
                                <div class="detail-item"> <span>${d.wifi}</span></div>
                                <div class="detail-item">Коорд: <span>${d.lat.toFixed(4)}, ${d.lng.toFixed(4)}</span></div>
                                <div class="detail-item">Время: <span>${d.last_seen}</span></div>
                            </div>
                        </div>`;
                    }

                    document.getElementById('target-count').innerText = `${activeCount} `;
                    if (html) document.getElementById('list').innerHTML = html;

                } catch(e) {
                    console.error(e);
                }
            }

            setInterval(updateMap, 1000);
        </script>
    </body>
    </html>
    """

