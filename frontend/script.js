let audioEnabled = true;
let audioContext = null;
let lastProcessedId = 0;

function getAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
    return audioContext;
}

function toggleAudio() {
    getAudioContext();
    audioEnabled = !audioEnabled;
    const btn = document.getElementById('sirenToggle');
    btn.innerText = audioEnabled ? "Siren: ON" : "Siren: OFF";
    btn.style.background = audioEnabled ? "#2ec4b6" : "#4a5568";
}

function soundEmergencySiren() {
    if (!audioEnabled) return;
    try {
        const ctx = getAudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = "sawtooth";
        const now = ctx.currentTime;
        osc.frequency.setValueAtTime(900, now);
        osc.frequency.exponentialRampToValueAtTime(450, now + 0.3);
        osc.frequency.exponentialRampToValueAtTime(900, now + 0.6);

        gain.gain.setValueAtTime(0.3, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.7);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.7);
    } catch (err) {
        console.warn("Audio synthesizer notice:", err);
    }
}

function triggerScreenFlash() {
    const flash = document.getElementById('flashOverlay');
    flash.style.display = 'block';
    setTimeout(() => {
        flash.style.display = 'none';
    }, 450);
}

const map = L.map('map').setView([26.7271, 88.3953], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'OpenStreetMap',
    maxZoom: 18
}).addTo(map);

let corridorMarkers = [];

function convertToIST(utcString) {
    if (!utcString) return "--:--:--";
    const dateObj = new Date(utcString.endsWith('Z') ? utcString : utcString + 'Z');
    if (isNaN(dateObj.getTime())) return utcString;
    return dateObj.toLocaleTimeString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour12: true,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 1. Check System Status (/status)
async function syncSystemStatus() {
    try {
        const response = await fetch('/status');
        if (!response.ok) throw new Error('Network response not ok');
        const statusData = await response.json();

        document.getElementById('backendStatus').innerHTML = `Backend: <span style="color:#2ec4b6;">${statusData.backend.toUpperCase()}</span>`;
        document.getElementById('dbStatus').innerHTML = `DB: <span style="color:#2ec4b6;">${statusData.database.toUpperCase()}</span>`;
        document.getElementById('cameraStatus').innerHTML = `Feed: <span style="color:#2ec4b6;">${statusData.camera.toUpperCase()}</span>`;
    } catch (e) {
        document.getElementById('backendStatus').innerHTML = `Backend: <span style="color:#e63946;">OFFLINE</span>`;
        document.getElementById('dbStatus').innerHTML = `DB: <span style="color:#e63946;">DISCONNECTED</span>`;
    }
}

// 2. Poll Latest Alert (/latest)
async function pollLatestDetection() {
    try {
        const response = await fetch('/latest');
        if (!response.ok) return;
        const latest = await response.json();

        if (latest.id && latest.id !== lastProcessedId) {
            lastProcessedId = latest.id;

            document.getElementById('latestId').innerText = `#${latest.id}`;
            document.getElementById('latestHerd').innerText = latest.elephant_count || 1;
            document.getElementById('latestConfidence').innerText = Number(latest.confidence).toFixed(2);

            if (latest.flash || latest.alert) {
                triggerScreenFlash();
                soundEmergencySiren();

                const banner = document.getElementById('alertBanner');
                banner.style.display = 'flex';
                document.getElementById('bannerDetails').innerText = 
                    `Sighting #${latest.id}: Herd size ${latest.elephant_count} detected with ${(latest.confidence * 100).toFixed(0)}% confidence at GPS (${latest.latitude.toFixed(4)}, ${latest.longitude.toFixed(4)})`;

                setTimeout(() => {
                    banner.style.display = 'none';
                }, 6000);
            }
        }
    } catch (e) {
        console.error("Failed to poll /latest:", e);
    }
}

// 3. Load Incident History (/detections)
async function loadDetectionHistory() {
    try {
        const response = await fetch('/detections');
        if (!response.ok) throw new Error('History fetch failed');
        const detections = await response.json();

        document.getElementById('totalIncidents').innerText = detections.length;

        corridorMarkers.forEach(m => map.removeLayer(m));
        corridorMarkers = [];

        const tableBody = document.getElementById('historyTableBody');
        tableBody.innerHTML = '';

        if (detections.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="loading-cell" style="text-align:center; padding: 16px;">No elephant sightings logged yet. Run predict_video.py to detect.</td></tr>';
            return;
        }

        detections.forEach((item, index) => {
            if (index === 0) {
                const marker = L.circleMarker([item.latitude, item.longitude], {
                    color: '#e63946',
                    fillColor: '#e63946',
                    fillOpacity: 0.85,
                    radius: 9
                }).addTo(map);
                marker.bindPopup(`<b>Incident #${item.id}</b><br>Herd Count: ${item.elephant_count}<br>Confidence: ${item.confidence}`).openPopup();
                corridorMarkers.push(marker);
            }

            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>#${item.id}</strong></td>
                <td>${convertToIST(item.timestamp)}</td>
                <td>${Number(item.latitude).toFixed(4)}, ${Number(item.longitude).toFixed(4)}</td>
                <td>${(Number(item.confidence) * 100).toFixed(1)}%</td>
                <td><span class="badge-herd">${item.elephant_count}</span></td>
                <td>${item.source}</td>
                <td><span class="status-badge-ok" style="color:#2ec4b6; font-weight:bold;">LOGGED</span></td>
            `;
            tableBody.appendChild(row);
        });
    } catch (e) {
        console.error("Failed to fetch /detections:", e);
    }
}

setInterval(() => {
    const now = new Date();
    document.getElementById('hudTimestamp').innerText = now.toLocaleTimeString('en-IN', { hour12: false });
}, 1000);

document.body.addEventListener('click', getAudioContext, { once: true });
syncSystemStatus();
pollLatestDetection();
loadDetectionHistory();

setInterval(syncSystemStatus, 4000);
setInterval(pollLatestDetection, 1500);
setInterval(loadDetectionHistory, 3000);
