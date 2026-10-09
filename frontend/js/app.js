// NER Hub Coordinates Dictionary
const NER_HUBS = {
    "Guwahati": [26.1445, 91.7362],
    "Shillong": [25.5788, 91.8933],
    "Tezpur": [26.6528, 92.7926],
    "Silchar": [24.8333, 92.7789],
    "Itanagar": [27.0844, 93.6053],
    "Imphal": [24.8170, 93.9368],
    "Kohima": [25.6751, 94.1086],
    "Aizawl": [23.7271, 92.7176],
    "Agartala": [23.8315, 91.2868],
    "Gangtok": [27.3389, 88.6065],
    "Dibrugarh": [27.4728, 94.9120],
    "Dimapur": [25.9060, 93.7271],
    "Jorhat": [26.7509, 94.2037],
    "Tura": [25.5141, 90.2032]
};

let map = null;
let shortestPolyline = null;
let riskAwarePolyline = null;
let hubMarkers = [];

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    setupEventListeners();
});

function initMap() {
    // Center map on North Eastern Region (Guwahati reference)
    map = L.map("map").setView([26.1445, 91.7362], 7);

    // OpenStreetMap Tile Layer
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
    }).addTo(map);

    // Render Hub Markers
    Object.keys(NER_HUBS).forEach((hubName) => {
        const coords = NER_HUBS[hubName];
        const marker = L.circleMarker(coords, {
            radius: 7,
            fillColor: "#38bdf8",
            color: "#0f172a",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
        }).addTo(map);

        marker.bindPopup(`<b>Hub:</b> ${hubName}`);
        hubMarkers.push(marker);
    });
}

function setupEventListeners() {
    const calculateBtn = document.getElementById("calculate-btn");
    if (calculateBtn) {
        calculateBtn.addEventListener("click", handleCalculateRoutes);
    }

    const riskBtn = document.getElementById("risk-btn");
    if (riskBtn) {
        riskBtn.addEventListener("click", handleEvaluateRisk);
    }
}

async function handleCalculateRoutes() {
    const origin = document.getElementById("origin-select").value;
    const destination = document.getElementById("destination-select").value;
    const preference = document.getElementById("preference-select").value;

    if (origin === destination) {
        showStatus("Origin and Destination must be different hubs.", "error");
        return;
    }

    showStatus("Computing optimal risk-aware routing...", "loading");

    try {
        const response = await fetch("/route/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                origin: origin,
                destination: destination,
                preference: preference
            })
        });

        const data = await response.json();

        if (!response.ok || data.status === "unavailable") {
            showStatus(data.message || "Route unavailable between selected hubs.", "error");
            clearMapRoutes();
            hideResultsPanel();
            return;
        }

        renderRoutesOnMap(data);
        displayRouteMetrics(data);
        showStatus(`Route successfully calculated between ${origin} and ${destination}.`, "success");
    } catch (err) {
        showStatus("Failed to connect to routing API service.", "error");
        console.error("Routing API Error:", err);
    }
}

function renderRoutesOnMap(data) {
    clearMapRoutes();

    const shortest = data.shortest_route;
    const riskAware = data.risk_aware_route;

    // Render Shortest Polyline (Blue)
    if (shortest && shortest.geometry && shortest.geometry.length > 0) {
        shortestPolyline = L.polyline(shortest.geometry, {
            color: "#38bdf8",
            weight: 5,
            opacity: 0.8,
            dashArray: "6, 6"
        }).addTo(map);
    }

    // Render Risk-Aware Polyline (Green/Yellow/Red)
    if (riskAware && riskAware.geometry && riskAware.geometry.length > 0) {
        let routeColor = "#4ade80"; // Green
        if (riskAware.risk_level === "MEDIUM") routeColor = "#fbbf24";
        if (riskAware.risk_level === "HIGH") routeColor = "#f87171";

        riskAwarePolyline = L.polyline(riskAware.geometry, {
            color: routeColor,
            weight: 6,
            opacity: 0.9
        }).addTo(map);

        map.fitBounds(riskAwarePolyline.getBounds(), { padding: [40, 40] });
    }
}

function displayRouteMetrics(data) {
    const resultsPanel = document.getElementById("results-panel");
    resultsPanel.classList.remove("hidden");

    const shortest = data.shortest_route;
    const riskAware = data.risk_aware_route;

    if (shortest) {
        document.getElementById("shortest-dist").textContent = `${shortest.distance_km} km`;
        document.getElementById("shortest-time").textContent = `${Math.floor(shortest.travel_time_min / 60)}h ${shortest.travel_time_min % 60}m`;
        document.getElementById("shortest-risk").textContent = `${(shortest.risk_score * 100).toFixed(1)}%`;
        document.getElementById("shortest-path").textContent = shortest.path.join(" -> ");
    }

    if (riskAware) {
        document.getElementById("risk-dist").textContent = `${riskAware.distance_km} km`;
        document.getElementById("risk-time").textContent = `${Math.floor(riskAware.travel_time_min / 60)}h ${riskAware.travel_time_min % 60}m`;
        
        const badgeEl = document.getElementById("risk-level");
        badgeEl.textContent = riskAware.risk_level;
        badgeEl.className = `badge ${riskAware.risk_level.toLowerCase()}`;

        document.getElementById("risk-path").textContent = riskAware.path.join(" -> ");
    }
}

function clearMapRoutes() {
    if (shortestPolyline) {
        map.removeLayer(shortestPolyline);
        shortestPolyline = null;
    }
    if (riskAwarePolyline) {
        map.removeLayer(riskAwarePolyline);
        riskAwarePolyline = null;
    }
}

function hideResultsPanel() {
    const resultsPanel = document.getElementById("results-panel");
    resultsPanel.classList.add("hidden");
}

function showStatus(message, type) {
    const banner = document.getElementById("status-banner");
    banner.textContent = message;
    banner.className = `status-banner ${type}`;
}

async function handleEvaluateRisk() {
    const rainfall = parseFloat(document.getElementById("rainfall-input").value) || 0;
    const waterLevel = parseFloat(document.getElementById("water-level-input").value) || 0;
    const discharge = parseFloat(document.getElementById("discharge-input").value) || 0;
    const elevation = parseFloat(document.getElementById("elevation-input").value) || 0;
    const landCover = document.getElementById("land-cover-select").value;
    const soilType = document.getElementById("soil-type-select").value;

    try {
        const response = await fetch("/predict/environmental-risk", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                rainfall_mm: rainfall,
                water_level_m: waterLevel,
                river_discharge_m3s: discharge,
                elevation_m: elevation,
                land_cover: landCover,
                soil_type: soilType
            })
        });

        const data = await response.json();

        if (response.ok) {
            const riskOutput = document.getElementById("risk-output");
            riskOutput.classList.remove("hidden");

            document.getElementById("env-prob-val").textContent = `${(data.probability * 100).toFixed(1)}%`;
            
            const levelEl = document.getElementById("env-level-val");
            levelEl.textContent = data.risk_level;
            levelEl.className = `badge ${data.risk_level.toLowerCase()}`;

            const factorsUl = document.getElementById("env-factors-ul");
            factorsUl.innerHTML = "";
            (data.key_factors || []).forEach((factor) => {
                const li = document.createElement("li");
                li.textContent = factor;
                factorsUl.appendChild(li);
            });
        }
    } catch (err) {
        console.error("Risk evaluation failed:", err);
    }
}
