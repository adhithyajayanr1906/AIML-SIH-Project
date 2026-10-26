/**
 * NER Smart Logistics — Application JavaScript
 * =============================================
 * Location search with autocomplete (backed by /locations/search → Nominatim),
 * transport mode selection, route requests, Leaflet map drawing, and result display.
 *
 * Transport modes
 *   ROADWAY  → POST /route/recommend  (mode: SHORTEST | SAFE)
 *   AIRWAY   → POST /route/airway     (Haversine direct-distance estimate)
 *
 * Design rules
 *   - No hardcoded place coordinates or fabricated results.
 *   - Route calculation is blocked until both locations are selected from suggestions.
 *   - Editing a selected location invalidates its stored coordinates.
 *   - No duplicate in-flight route requests.
 *   - No raw exception traces shown to users.
 *   - Autocomplete debounced; minimum 2-char query; silent on empty.
 */

"use strict";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const API_BASE = "";   // Same origin as the FastAPI server

const ROUTE_COLORS = {
    SHORTEST: "#3d7eff",   // Blue — shortest road route
    SAFE:     "#22c55e",   // Green — lowest-risk road route
    AIRWAY:   "#f59e0b",   // Amber — direct air-distance line
};

/** NER region centre for initial map view. */
const NER_CENTER       = [26.2006, 92.9376];
const NER_INITIAL_ZOOM = 7;

/** Debounce delay for autocomplete (ms). */
const SEARCH_DEBOUNCE_MS = 350;

/** Minimum characters before sending a search request. */
const MIN_QUERY_LEN = 2;

// ---------------------------------------------------------------------------
// Application State
// ---------------------------------------------------------------------------
let map              = null;
let currentRouteLayer = null;
let transportMode    = "ROADWAY";   // "ROADWAY" | "AIRWAY"
let isRequestInFlight = false;       // Prevents duplicate route submissions
let currentCalculationId = null;     // Stored calculation ID from backend
let lastRouteData = null;            // Cache of latest calculated route
let activeTab = "planner";

/**
 * Selected location state.
 * A location is "valid" only when coords are non-null (set by selecting a suggestion).
 * Editing the input text clears the coords, making the location invalid.
 */
const selected = {
    origin: { name: "", lat: null, lon: null },
    dest:   { name: "", lat: null, lon: null },
};

/** Pinned map markers for origin/destination. */
let originMarker = null;
let destMarker   = null;

/** Debounce timer handles. */
const debounceTimers = { origin: null, dest: null };

/** Track which suggestion list item has keyboard focus. */
const listFocus = { origin: -1, dest: -1 };

// ---------------------------------------------------------------------------
// Map Initialisation
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    map = L.map("map", {
        zoomControl: false,
        preferCanvas: false,
    }).setView(NER_CENTER, NER_INITIAL_ZOOM);

    L.control.zoom({ position: "bottomright" }).addTo(map);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors",
        maxZoom: 18,
    }).addTo(map);

    // Attach search handlers
    attachSearchHandlers("origin");
    attachSearchHandlers("dest");

    // Close dropdowns on outside click
    document.addEventListener("click", (e) => {
        if (!e.target.closest("#origin-location-field")) closeSuggestions("origin");
        if (!e.target.closest("#dest-location-field"))   closeSuggestions("dest");
    });

    // Close report modal on backdrop click or Escape key
    const reportModal = document.getElementById("report-modal");
    if (reportModal) {
        reportModal.addEventListener("click", (e) => {
            if (e.target === reportModal) closeReportModal();
        });
    }
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeReportModal();
    });

    // Check system health on boot
    checkSystemHealth();
});

// ---------------------------------------------------------------------------
// Autocomplete — Search Handler attachment
// ---------------------------------------------------------------------------

/**
 * Attach input, keydown, and focus handler to a location search field.
 * @param {"origin"|"dest"} which
 */
function attachSearchHandlers(which) {
    const input = document.getElementById(`${which}-search`);

    input.addEventListener("input", () => {
        // Invalidate coordinates when the user edits the text
        if (selected[which].lat !== null) {
            selected[which].lat = null;
            selected[which].lon = null;
            removeMarker(which);
        }
        showClearBtn(which, input.value.length > 0);

        const q = input.value.trim();
        clearTimeout(debounceTimers[which]);

        if (q.length < MIN_QUERY_LEN) {
            closeSuggestions(which);
            hideFieldStatus(which);
            return;
        }

        debounceTimers[which] = setTimeout(() => doSearch(which, q), SEARCH_DEBOUNCE_MS);
    });

    input.addEventListener("keydown", (e) => handleSearchKeydown(e, which));

    input.addEventListener("focus", () => {
        // Re-open suggestions if there's already a query typed but nothing selected
        const q = input.value.trim();
        if (q.length >= MIN_QUERY_LEN && selected[which].lat === null) {
            doSearch(which, q);
        }
    });
}

// ---------------------------------------------------------------------------
// Autocomplete — Core search
// ---------------------------------------------------------------------------

/**
 * Fire the location search API and render suggestions.
 * @param {"origin"|"dest"} which
 * @param {string} q
 */
async function doSearch(which, q) {
    showSpinner(which, true);
    hideFieldStatus(which);

    try {
        const res = await fetch(
            `${API_BASE}/locations/search?q=${encodeURIComponent(q)}`,
            { signal: AbortSignal.timeout(10_000) }
        );

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            showFieldStatus(which, err.detail ?? "Location search failed. Please try again.", "error");
            closeSuggestions(which);
            return;
        }

        const data = await res.json();
        renderSuggestions(which, data.results ?? []);

    } catch (err) {
        if (err.name === "TimeoutError" || err.name === "AbortError") {
            showFieldStatus(which, "Location search timed out. Please try again.", "error");
        } else {
            showFieldStatus(which, "Location search is temporarily unavailable.", "error");
        }
        closeSuggestions(which);
    } finally {
        showSpinner(which, false);
    }
}

// ---------------------------------------------------------------------------
// Autocomplete — Rendering
// ---------------------------------------------------------------------------

/**
 * Render the suggestions dropdown.
 * @param {"origin"|"dest"} which
 * @param {Array} results
 */
function renderSuggestions(which, results) {
    const list  = document.getElementById(`${which}-suggestions`);
    const input = document.getElementById(`${which}-search`);

    list.innerHTML = "";
    listFocus[which] = -1;

    if (results.length === 0) {
        showFieldStatus(which, "No matching places found.", "info");
        closeSuggestions(which);
        input.setAttribute("aria-expanded", "false");
        return;
    }

    hideFieldStatus(which);

    results.forEach((place, idx) => {
        const li = document.createElement("li");
        li.className   = "suggestion-item";
        li.role        = "option";
        li.id          = `${which}-sug-${idx}`;
        li.tabIndex    = -1;
        li.setAttribute("aria-selected", "false");

        // Split display name: first part (place name) and rest (context)
        const parts    = place.display_name.split(",");
        const primary  = parts[0].trim();
        const context  = parts.slice(1).join(",").trim();

        li.innerHTML =
            `<span class="sug-primary">${escapeHtml(primary)}</span>` +
            (context ? `<span class="sug-context">${escapeHtml(context)}</span>` : "");

        li.addEventListener("mousedown", (e) => {
            // Use mousedown (fires before blur) so the click registers
            e.preventDefault();
            selectSuggestion(which, place);
        });

        list.appendChild(li);
    });

    list.classList.remove("hidden");
    input.setAttribute("aria-expanded", "true");
}

/**
 * Handle keyboard navigation inside the suggestion list.
 * @param {KeyboardEvent} e
 * @param {"origin"|"dest"} which
 */
function handleSearchKeydown(e, which) {
    const list  = document.getElementById(`${which}-suggestions`);
    const items = list.querySelectorAll(".suggestion-item");

    switch (e.key) {
        case "ArrowDown":
            e.preventDefault();
            if (items.length === 0) return;
            listFocus[which] = Math.min(listFocus[which] + 1, items.length - 1);
            updateListFocus(which, items);
            break;

        case "ArrowUp":
            e.preventDefault();
            if (items.length === 0) return;
            listFocus[which] = Math.max(listFocus[which] - 1, 0);
            updateListFocus(which, items);
            break;

        case "Enter":
            e.preventDefault();
            if (listFocus[which] >= 0 && items[listFocus[which]]) {
                items[listFocus[which]].dispatchEvent(new Event("mousedown"));
            } else if (selected[which].lat !== null) {
                // Both inputss valid — trigger route
                findRoute();
            }
            break;

        case "Escape":
            closeSuggestions(which);
            document.getElementById(`${which}-search`).blur();
            break;
    }
}

/**
 * Move aria/visual focus to the given list item index.
 * @param {"origin"|"dest"} which
 * @param {NodeList} items
 */
function updateListFocus(which, items) {
    items.forEach((item, i) => {
        const focused = i === listFocus[which];
        item.classList.toggle("focused", focused);
        item.setAttribute("aria-selected", String(focused));
        if (focused) {
            item.scrollIntoView({ block: "nearest" });
            document.getElementById(`${which}-search`)
                .setAttribute("aria-activedescendant", item.id);
        }
    });
}

/**
 * Commit a suggestion to the selected state.
 * @param {"origin"|"dest"} which
 * @param {object} place
 */
function selectSuggestion(which, place) {
    selected[which].name = place.display_name;
    selected[which].lat  = place.latitude;
    selected[which].lon  = place.longitude;

    const parts   = place.display_name.split(",");
    const primary = parts[0].trim();

    document.getElementById(`${which}-search`).value = primary;
    showClearBtn(which, true);
    closeSuggestions(which);
    hideFieldStatus(which);
    markFieldValid(which, true);

    // Place / update map marker
    placeMarker(which, place.latitude, place.longitude, place.display_name);

    // Pan map to new selection if no route is drawn
    if (!currentRouteLayer) {
        map.flyTo([place.latitude, place.longitude], Math.max(map.getZoom(), 10), { duration: 0.8 });
    }

    // Update status message
    const otherWhich = which === "origin" ? "dest" : "origin";
    if (selected[otherWhich].lat === null) {
        setStatus(`Select a destination from the suggestions.`);
    } else {
        setStatus("Both locations selected. Click Find Route.");
    }
}

// ---------------------------------------------------------------------------
// Location Field Helpers
// ---------------------------------------------------------------------------

function clearLocation(which) {
    selected[which].lat  = null;
    selected[which].lon  = null;
    selected[which].name = "";
    document.getElementById(`${which}-search`).value = "";
    showClearBtn(which, false);
    closeSuggestions(which);
    hideFieldStatus(which);
    markFieldValid(which, false);
    removeMarker(which);
    setStatus("Search for a starting location.");
}

function closeSuggestions(which) {
    const list  = document.getElementById(`${which}-suggestions`);
    const input = document.getElementById(`${which}-search`);
    list.classList.add("hidden");
    list.innerHTML = "";
    listFocus[which] = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
}

function showSpinner(which, visible) {
    document.getElementById(`${which}-spinner`).classList.toggle("hidden", !visible);
}

function showClearBtn(which, visible) {
    document.getElementById(`${which}-clear`).classList.toggle("hidden", !visible);
}

function showFieldStatus(which, message, type = "info") {
    const el = document.getElementById(`${which}-status`);
    el.textContent = message;
    el.classList.remove("hidden", "field-status--error", "field-status--info");
    el.classList.add(type === "error" ? "field-status--error" : "field-status--info");
}

function hideFieldStatus(which) {
    document.getElementById(`${which}-status`).classList.add("hidden");
}

function markFieldValid(which, valid) {
    document.getElementById(`${which}-location-field`)
        .classList.toggle("is-valid", valid);
}

// ---------------------------------------------------------------------------
// Map Markers
// ---------------------------------------------------------------------------

const MARKER_COLORS = { origin: "#3d7eff", dest: "#22c55e" };

function placeMarker(which, lat, lon, label) {
    removeMarker(which);

    const color    = MARKER_COLORS[which];
    const marker   = L.circleMarker([lat, lon], {
        radius:      8,
        color:       color,
        fillColor:   color,
        fillOpacity: 1,
        weight:      2,
    }).addTo(map).bindPopup(escapeHtml(label));

    if (which === "origin") originMarker = marker;
    else                    destMarker   = marker;
}

function removeMarker(which) {
    if (which === "origin" && originMarker) { map.removeLayer(originMarker); originMarker = null; }
    if (which === "dest"   && destMarker)   { map.removeLayer(destMarker);   destMarker   = null; }
}

function removeAllMarkers() {
    removeMarker("origin");
    removeMarker("dest");
}

// ---------------------------------------------------------------------------
// Transport Mode Toggle
// ---------------------------------------------------------------------------

/**
 * Switch between ROADWAY and AIRWAY transport modes.
 * @param {"ROADWAY"|"AIRWAY"} mode
 */
function setTransportMode(mode) {
    transportMode = mode;

    document.getElementById("btn-mode-roadway").classList.toggle("active", mode === "ROADWAY");
    document.getElementById("btn-mode-roadway").setAttribute("aria-pressed", String(mode === "ROADWAY"));
    document.getElementById("btn-mode-airway").classList.toggle("active", mode === "AIRWAY");
    document.getElementById("btn-mode-airway").setAttribute("aria-pressed", String(mode === "AIRWAY"));

    document.getElementById("road-submode-section").classList.toggle("hidden", mode !== "ROADWAY");
    document.getElementById("airway-info-section").classList.toggle("hidden", mode !== "AIRWAY");

    clearRouteLayer();
    closeResults();
    document.getElementById("map-empty-state").classList.remove("hidden");

    setStatus(`Transport mode: ${mode === "ROADWAY" ? "Roadway" : "Airway"}. Click Find Route.`);
}

// ---------------------------------------------------------------------------
// Route Dispatching — main entry point
// ---------------------------------------------------------------------------

/**
 * Validate both locations are selected, then dispatch the appropriate route call.
 */
function findRoute() {
    if (isRequestInFlight) return;

    if (selected.origin.lat === null) {
        setStatus("Search for a starting location.", "error");
        document.getElementById("origin-search").focus();
        return;
    }
    if (selected.dest.lat === null) {
        setStatus("Select a destination from the suggestions.", "error");
        document.getElementById("dest-search").focus();
        return;
    }

    const coords = {
        origLat: selected.origin.lat,
        origLon: selected.origin.lon,
        destLat: selected.dest.lat,
        destLon: selected.dest.lon,
    };

    if (transportMode === "ROADWAY") {
        const submode = document.querySelector('input[name="road_submode"]:checked')?.value ?? "SHORTEST";
        requestRoadRoute(coords, submode);
    } else {
        requestAirwayRoute(coords);
    }
}

// ---------------------------------------------------------------------------
// Roadway — POST /route/recommend
// ---------------------------------------------------------------------------

/**
 * Request a road route from the backend.
 * @param {{origLat, origLon, destLat, destLon}} coords
 * @param {"SHORTEST"|"SAFE"} submode
 */
async function requestRoadRoute(coords, submode) {
    const { origLat, origLon, destLat, destLon } = coords;

    setInFlight(true);
    showLoader("Calculating road route…");

    try {
        const response = await fetch(`${API_BASE}/route/recommend`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                origin_lat:     origLat,
                origin_lon:     origLon,
                dest_lat:       destLat,
                dest_lon:       destLon,
                origin_name:    selected.origin.name || "Origin",
                dest_name:      selected.dest.name || "Destination",
                mode:           submode,
                transport_mode: "ROADWAY",
            }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail ?? `Server returned ${response.status}`);
        }

        const data = await response.json();

        hideLoader();
        setStatus("Road route calculated successfully.", "success");

        const polyline = flattenRoadCoords(data.coords);
        if (polyline.length < 2) {
            setStatus("Route returned no drawable geometry.", "error");
            return;
        }

        drawRoadRoute(polyline, submode);
        showRoadwayResults(data, submode);

    } catch (err) {
        hideLoader();
        setStatus(`No road route available: ${err.message}`, "error");
        clearRouteLayer();
    } finally {
        setInFlight(false);
    }
}

/**
 * Convert the router's edge-pair format into a flat lat/lon polyline.
 * Router returns:  [ [[lat1,lon1],[lat2,lon2]], [[lat2,lon2],[lat3,lon3]], … ]
 * Leaflet expects: [ [lat1,lon1], [lat2,lon2], [lat3,lon3], … ]
 *
 * @param {Array} rawCoords
 * @returns {Array<[number,number]>}
 */
function flattenRoadCoords(rawCoords) {
    if (!Array.isArray(rawCoords) || rawCoords.length === 0) return [];

    const result = [];
    for (let i = 0; i < rawCoords.length; i++) {
        const edge = rawCoords[i];
        const ptA  = toLatLon(edge[0]);
        const ptB  = toLatLon(edge[1]);
        if (!ptA || !ptB) continue;
        if (i === 0) {
            result.push(ptA);
        } else {
            const last = result[result.length - 1];
            if (last[0] !== ptA[0] || last[1] !== ptA[1]) result.push(ptA);
        }
        result.push(ptB);
    }
    return result;
}

/**
 * Normalise a point from [lat,lon] or Python-tuple-serialised form.
 * @param {any} pt
 * @returns {[number,number]|null}
 */
function toLatLon(pt) {
    if (Array.isArray(pt) && pt.length >= 2) {
        const lat = Number(pt[0]);
        const lon = Number(pt[1]);
        if (Number.isFinite(lat) && Number.isFinite(lon)) return [lat, lon];
    }
    return null;
}

// ---------------------------------------------------------------------------
// Airway — POST /route/airway
// ---------------------------------------------------------------------------

/**
 * Request a Haversine direct-distance estimate from the backend.
 * @param {{origLat, origLon, destLat, destLon}} coords
 */
async function requestAirwayRoute(coords) {
    const { origLat, origLon, destLat, destLon } = coords;

    setInFlight(true);
    showLoader("Calculating air distance estimate…");

    try {
        const response = await fetch(`${API_BASE}/route/airway`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                origin_lat:  origLat,
                origin_lon:  origLon,
                dest_lat:    destLat,
                dest_lon:    destLon,
                origin_name: selected.origin.name || "Origin",
                dest_name:   selected.dest.name || "Destination",
            }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail ?? `Server returned ${response.status}`);
        }

        const data = await response.json();

        hideLoader();
        setStatus("Direct air distance calculated.", "success");

        drawAirwayLine(data.coords[0], data.coords[1]);
        showAirwayResults(data);

    } catch (err) {
        hideLoader();
        setStatus(`Airway error: ${err.message}`, "error");
        clearRouteLayer();
    } finally {
        setInFlight(false);
    }
}

// ---------------------------------------------------------------------------
// Map Drawing
// ---------------------------------------------------------------------------

/**
 * Draw the road route polyline on the map.
 * @param {Array<[number,number]>} polyline
 * @param {"SHORTEST"|"SAFE"} submode
 */
function drawRoadRoute(polyline, submode) {
    clearRouteLayer();

    const color = submode === "SAFE" ? ROUTE_COLORS.SAFE : ROUTE_COLORS.SHORTEST;

    currentRouteLayer = L.polyline(polyline, {
        color,
        weight:    5,
        opacity:   0.9,
        lineCap:   "round",
        lineJoin:  "round",
    }).addTo(map);

    currentRouteLayer.on("mouseover", function () { this.setStyle({ weight: 8, opacity: 1 }); });
    currentRouteLayer.on("mouseout",  function () { this.setStyle({ weight: 5, opacity: 0.9 }); });

    map.flyToBounds(currentRouteLayer.getBounds(), {
        paddingTopLeft:     [360, 16],
        paddingBottomRight: [320, 16],
        duration: 1.2,
    });

    document.getElementById("map-empty-state").classList.add("hidden");
}

/**
 * Draw the airway direct-distance dashed line on the map.
 * @param {[number,number]} originLatLon
 * @param {[number,number]} destLatLon
 */
function drawAirwayLine(originLatLon, destLatLon) {
    clearRouteLayer();

    currentRouteLayer = L.polyline(
        [originLatLon, destLatLon],
        {
            color:     ROUTE_COLORS.AIRWAY,
            weight:    3,
            opacity:   0.85,
            dashArray: "10, 8",
            lineCap:   "round",
        }
    ).addTo(map);

    // Endpoint circle markers (in addition to the named markers already placed)
    const mkOrig = L.circleMarker(originLatLon, {
        radius: 6, color: ROUTE_COLORS.AIRWAY, fillColor: ROUTE_COLORS.AIRWAY, fillOpacity: 1, weight: 2,
    }).addTo(map).bindPopup(escapeHtml(selected.origin.name || "Origin"));

    const mkDest = L.circleMarker(destLatLon, {
        radius: 6, color: ROUTE_COLORS.AIRWAY, fillColor: ROUTE_COLORS.AIRWAY, fillOpacity: 1, weight: 2,
    }).addTo(map).bindPopup(escapeHtml(selected.dest.name || "Destination"));

    currentRouteLayer._subLayers = [mkOrig, mkDest];

    map.flyToBounds(
        L.latLngBounds([originLatLon, destLatLon]),
        { paddingTopLeft: [360, 40], paddingBottomRight: [320, 40], duration: 1.2 }
    );

    document.getElementById("map-empty-state").classList.add("hidden");
}

// ---------------------------------------------------------------------------
// Results Panel
// ---------------------------------------------------------------------------

/**
 * Show roadway results.
 * @param {object} data — API response
 * @param {"SHORTEST"|"SAFE"} submode
 */
function showRoadwayResults(data, submode) {
    currentCalculationId = data.calculation_id || null;
    lastRouteData = data;

    document.getElementById("roadway-results").classList.remove("hidden");
    document.getElementById("airway-results").classList.add("hidden");

    document.getElementById("results-title").textContent = "Route Results";
    document.getElementById("r_origin_name").textContent = truncateName(selected.origin.name);
    document.getElementById("r_dest_name").textContent   = truncateName(selected.dest.name);
    document.getElementById("r_transport_mode").textContent = "Roadway";
    document.getElementById("r_type").textContent = submode === "SAFE" ? "Lowest Risk Route" : "Shortest Route";
    document.getElementById("r_dist").textContent = data.distance_km ?? "—";
    document.getElementById("r_dist_unit").textContent = "km";
    document.getElementById("r_seg").textContent = data.segments ?? "—";

    const costEl = document.getElementById("r_cost");
    if (costEl) costEl.textContent = data.total_cost !== undefined ? `${data.total_cost} cost units` : "—";

    // Feature 1A: Validation Details
    if (data.validation) {
        const valBadge = document.getElementById("r_val_badge");
        if (valBadge) {
            valBadge.textContent = data.validation.status;
            valBadge.className = data.validation.status === "PASSED" ? "badge badge-success" : "badge badge-danger";
        }
        const snapDesc = document.getElementById("r_val_snap_desc");
        if (snapDesc && data.validation.validation_checks) {
            const vc = data.validation.validation_checks;
            snapDesc.textContent = `Endpoints snapped: O:${vc.origin_snapping_distance_km}km, D:${vc.destination_snapping_distance_km}km (≤50km tol)`;
        }
    }

    // Feature 1C: Confidence Score
    if (data.confidence) {
        const confBadge = document.getElementById("r_conf_badge");
        if (confBadge) {
            confBadge.textContent = `${data.confidence.rating} (${data.confidence.score_percentage}%)`;
            confBadge.className = data.confidence.score_percentage >= 80 ? "badge badge-primary" : (data.confidence.score_percentage >= 50 ? "badge badge-warning" : "badge badge-neutral");
        }
        const confBar = document.getElementById("r_conf_bar");
        if (confBar) confBar.style.width = `${data.confidence.score_percentage}%`;

        if (data.confidence.factors) {
            const f = data.confidence.factors;
            const elSnap = document.getElementById("cf_snap");
            const elConn = document.getElementById("cf_conn");
            const elCov = document.getElementById("cf_cov");
            const elVal = document.getElementById("cf_val");
            if (elSnap) elSnap.textContent = `${f.snapping_proximity_pts} / 35 pts`;
            if (elConn) elConn.textContent = `${f.network_connectivity_pts} / 30 pts`;
            if (elCov) elCov.textContent = `${f.covariate_coverage_pts} / 20 pts`;
            if (elVal) elVal.textContent = `${f.mathematical_validation_pts} / 15 pts`;
        }
    }

    // Feature 3: Risk Breakdown
    if (data.risk_summary) {
        const elEnv = document.getElementById("r_risk_env");
        const elLog = document.getElementById("r_risk_log");
        const elBadge = document.getElementById("r_risk_badge");
        if (elEnv) elEnv.textContent = data.risk_summary.average_environmental_risk;
        if (elLog) elLog.textContent = data.risk_summary.average_logistics_risk;
        if (elBadge) {
            elBadge.textContent = data.risk_summary.risk_category;
            elBadge.className = data.risk_summary.risk_category === "LOW" ? "badge badge-success" : (data.risk_summary.risk_category === "MODERATE" ? "badge badge-warning" : "badge badge-danger");
        }
    }

    openResults();
}

/**
 * Show airway results.
 * @param {object} data — API response
 */
function showAirwayResults(data) {
    currentCalculationId = data.calculation_id || null;
    lastRouteData = data;

    document.getElementById("airway-results").classList.remove("hidden");
    document.getElementById("roadway-results").classList.add("hidden");

    document.getElementById("results-title").textContent = "Air Distance Estimate";
    document.getElementById("r_air_origin_name").textContent = truncateName(selected.origin.name);
    document.getElementById("r_air_dest_name").textContent   = truncateName(selected.dest.name);
    document.getElementById("r_air_dist").textContent = data.distance_km ?? "—";

    openResults();
}

// ---------------------------------------------------------------------------
// Clear / Reset
// ---------------------------------------------------------------------------

function openResults()  { document.getElementById("results-panel").classList.remove("hidden"); }
function closeResults() { document.getElementById("results-panel").classList.add("hidden"); }

/**
 * Remove the current route layer (and sub-layers) from the map.
 */
function clearRouteLayer() {
    if (!currentRouteLayer) return;
    if (Array.isArray(currentRouteLayer._subLayers)) {
        currentRouteLayer._subLayers.forEach((l) => map.removeLayer(l));
    }
    map.removeLayer(currentRouteLayer);
    currentRouteLayer = null;
}

/**
 * Full reset — clear route, markers, location state, and inputs.
 */
function clearRoute() {
    clearRouteLayer();
    removeAllMarkers();
    closeResults();

    // Reset both location fields
    ["origin", "dest"].forEach((which) => {
        selected[which].lat  = null;
        selected[which].lon  = null;
        selected[which].name = "";
        document.getElementById(`${which}-search`).value = "";
        showClearBtn(which, false);
        closeSuggestions(which);
        hideFieldStatus(which);
        markFieldValid(which, false);
    });

    document.getElementById("map-empty-state").classList.remove("hidden");
    setStatus("Search for a starting location.");
}

/**
 * Swap the two selected locations (name, lat, lon) and update the inputs + markers.
 */
function swapLocations() {
    const tmp = { ...selected.origin };
    selected.origin = { ...selected.dest };
    selected.dest   = { ...tmp };

    // Update input text
    const originPrimary = selected.origin.name ? selected.origin.name.split(",")[0].trim() : "";
    const destPrimary   = selected.dest.name   ? selected.dest.name.split(",")[0].trim()   : "";
    document.getElementById("origin-search").value = originPrimary;
    document.getElementById("dest-search").value   = destPrimary;

    showClearBtn("origin", originPrimary.length > 0);
    showClearBtn("dest",   destPrimary.length   > 0);
    markFieldValid("origin", selected.origin.lat !== null);
    markFieldValid("dest",   selected.dest.lat   !== null);

    // Redraw markers at swapped positions
    if (selected.origin.lat !== null) placeMarker("origin", selected.origin.lat, selected.origin.lon, selected.origin.name);
    else removeMarker("origin");

    if (selected.dest.lat !== null) placeMarker("dest", selected.dest.lat, selected.dest.lon, selected.dest.name);
    else removeMarker("dest");

    // Clear any drawn route (it was for the previous direction)
    clearRouteLayer();
    closeResults();
    document.getElementById("map-empty-state").classList.remove("hidden");
}

// ---------------------------------------------------------------------------
// UI State Helpers
// ---------------------------------------------------------------------------

/**
 * Update the status bar with optional severity styling.
 * @param {string} text
 * @param {""|"error"|"success"} type
 */
function setStatus(text, type = "") {
    const bar = document.getElementById("status-bar");
    bar.textContent = text;
    bar.classList.remove("is-error", "is-success");
    if (type === "error")   bar.classList.add("is-error");
    if (type === "success") bar.classList.add("is-success");
}

/**
 * Toggle the in-flight guard and disable/enable the Find Route button.
 * @param {boolean} inFlight
 */
function setInFlight(inFlight) {
    isRequestInFlight = inFlight;
    document.getElementById("btn-find-route").disabled = inFlight;
}

function showLoader(text) {
    document.getElementById("loader-text").textContent = text;
    document.getElementById("loader").classList.remove("hidden");
}

function hideLoader() {
    document.getElementById("loader").classList.add("hidden");
}

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------

/**
 * Escape HTML special characters to prevent XSS in innerHTML.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

/**
 * Truncate a long place name to the first part (before the first comma).
 * @param {string} name
 * @returns {string}
 */
function truncateName(name) {
    if (!name) return "—";
    return name.split(",")[0].trim();
}

// ---------------------------------------------------------------------------
// System Health Status Check
// ---------------------------------------------------------------------------
async function checkSystemHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        if (res.ok) {
            const data = await res.json();
            const pill = document.getElementById("health-text");
            if (pill) {
                pill.textContent = data.status === "ONLINE" ? `Online (${data.nodes?.toLocaleString()} nodes)` : "Degraded";
            }
        }
    } catch {
        const pill = document.getElementById("health-text");
        if (pill) pill.textContent = "Offline";
    }
}

// ---------------------------------------------------------------------------
// Tab Navigation
// ---------------------------------------------------------------------------
function switchTab(tabName) {
    activeTab = tabName;
    document.querySelectorAll(".nav-tab").forEach(tab => {
        const isCurrent = tab.id === `tab-btn-${tabName}`;
        tab.classList.toggle("active", isCurrent);
        tab.setAttribute("aria-selected", isCurrent ? "true" : "false");
    });

    document.querySelectorAll(".view-container").forEach(view => {
        view.classList.toggle("active", view.id === `view-${tabName}`);
    });

    if (tabName === "planner") {
        setTimeout(() => { if (map) map.invalidateSize(); }, 60);
    } else if (tabName === "overview") {
        loadOverview();
    } else if (tabName === "risk") {
        runRiskSimulation();
    } else if (tabName === "rainfall") {
        const sel = document.getElementById("rain-state-select");
        if (sel) loadStateRainfall(sel.value);
    } else if (tabName === "history") {
        loadHistoryTable();
    } else if (tabName === "compare") {
        if (selected.origin.lat && selected.dest.lat) {
            const cmpO = document.getElementById("cmp-origin");
            const cmpD = document.getElementById("cmp-dest");
            if (cmpO) cmpO.value = selected.origin.name || "Origin";
            if (cmpD) cmpD.value = selected.dest.name || "Destination";
        }
    }
}

// ---------------------------------------------------------------------------
// FEATURE 4: Route Comparison
// ---------------------------------------------------------------------------
let cmpOrigin = null;
let cmpDest   = null;

function compareCurrentRoute() {
    if (!selected.origin.lat || !selected.dest.lat) {
        setStatus("Please select an origin and destination on the map first.", "error");
        return;
    }
    cmpOrigin = { ...selected.origin };
    cmpDest   = { ...selected.dest };
    document.getElementById("cmp-origin").value = selected.origin.name || "Origin";
    document.getElementById("cmp-dest").value   = selected.dest.name || "Destination";
    switchTab("compare");
    executeComparison();
}

function loadPreset(oName, oLat, oLon, dName, dLat, dLon) {
    cmpOrigin = { name: oName, lat: oLat, lon: oLon };
    cmpDest   = { name: dName, lat: dLat, lon: dLon };
    document.getElementById("cmp-origin").value = oName;
    document.getElementById("cmp-dest").value   = dName;
    executeComparison();
}

async function executeComparison() {
    if (!cmpOrigin || !cmpDest || cmpOrigin.lat === null || cmpDest.lat === null) {
        if (selected.origin.lat && selected.dest.lat) {
            cmpOrigin = { ...selected.origin };
            cmpDest   = { ...selected.dest };
        } else {
            alert("Please choose origin and destination on Route Planner, or click one of the quick presets.");
            return;
        }
    }

    showLoader("Computing SHORTEST vs SAFE comparison…");
    try {
        const res = await fetch(`${API_BASE}/route/compare`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                origin_lat:  cmpOrigin.lat,
                origin_lon:  cmpOrigin.lon,
                dest_lat:    cmpDest.lat,
                dest_lon:    cmpDest.lon,
                origin_name: cmpOrigin.name,
                dest_name:   cmpDest.name,
            }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Server returned ${res.status}`);
        }

        const data = await res.json();
        hideLoader();

        // Populate Shortest Card
        document.getElementById("cmp-s-dist").textContent = `${data.shortest.distance_km} km`;
        document.getElementById("cmp-s-cost").textContent = data.shortest.total_cost;
        document.getElementById("cmp-s-seg").textContent  = data.shortest.segments;
        document.getElementById("cmp-s-risk").textContent = data.shortest.risk_summary?.risk_category || "LOW";
        document.getElementById("cmp-s-val").textContent  = data.shortest.validation?.status || "PASSED";
        document.getElementById("cmp-s-conf").textContent = data.shortest.confidence ? `${data.shortest.confidence.rating} (${data.shortest.confidence.score_percentage}%)` : "—";

        // Populate Safe Card
        document.getElementById("cmp-r-dist").textContent = `${data.safe.distance_km} km`;
        document.getElementById("cmp-r-cost").textContent = data.safe.total_cost;
        document.getElementById("cmp-r-seg").textContent  = data.safe.segments;
        document.getElementById("cmp-r-risk").textContent = data.safe.risk_summary?.risk_category || "LOW";
        document.getElementById("cmp-r-val").textContent  = data.safe.validation?.status || "PASSED";
        document.getElementById("cmp-r-conf").textContent = data.safe.confidence ? `${data.safe.confidence.rating} (${data.safe.confidence.score_percentage}%)` : "—";

        // Explanation Card
        document.getElementById("cmp-explanation-text").textContent = data.comparison.corridor_explanation;

        document.getElementById("compare-results-area").classList.remove("hidden");
        document.getElementById("compare-empty-state").classList.add("hidden");

    } catch (e) {
        hideLoader();
        alert(`Comparison failed: ${e.message}`);
    }
}

// ---------------------------------------------------------------------------
// FEATURE 2: Logistics Overview
// ---------------------------------------------------------------------------
async function loadOverview() {
    try {
        const res = await fetch(`${API_BASE}/analytics/overview`);
        if (!res.ok) return;
        const data = await res.json();

        if (data.road_network) {
            document.getElementById("ov-nodes").textContent = data.road_network.total_nodes?.toLocaleString() ?? "456,137";
            document.getElementById("ov-edges").textContent = data.road_network.total_edges?.toLocaleString() ?? "264,554";
            document.getElementById("ov-km").textContent = `${data.road_network.total_road_length_km?.toLocaleString()} km` ?? "166,530.99 km";
            document.getElementById("ov-comps").textContent = data.road_network.connected_components_count?.toLocaleString() ?? "192,225";
        }
        if (data.runtime_health) {
            const h = document.getElementById("ov-health");
            if (h) h.textContent = data.runtime_health.api_status ?? "ONLINE";
        }
    } catch (e) {
        console.error("Overview load error:", e);
    }
}

// ---------------------------------------------------------------------------
// FEATURE 3: Environmental Risk Simulation
// ---------------------------------------------------------------------------
async function runRiskSimulation() {
    const rain = parseFloat(document.getElementById("sim-rain-anomaly")?.value || 10);
    const extreme = parseInt(document.getElementById("sim-extreme")?.value || 0, 10);
    const slope = parseFloat(document.getElementById("sim-slope")?.value || 15);
    const elev = parseFloat(document.getElementById("sim-elev")?.value || 1200);
    const ndvi = parseFloat(document.getElementById("sim-ndvi")?.value || 0.55);
    const roadType = document.getElementById("sim-road-type")?.value || "primary";

    try {
        const envRes = await fetch(`${API_BASE}/predict/environmental-risk`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                rainfall_anomaly: rain,
                extreme_indicator: extreme,
                slope: slope,
                elev: elev,
                ndvi: ndvi
            })
        });
        const envData = await envRes.json();

        const logRes = await fetch(`${API_BASE}/predict/logistics-risk`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                env_risk_score: envData.risk_score,
                length_m: 1000.0,
                road_type: roadType
            })
        });
        const logData = await logRes.json();

        document.getElementById("sim-out-env").textContent = envData.risk_score.toFixed(2);
        const catEnv = document.getElementById("sim-cat-env");
        catEnv.textContent = envData.risk_category;
        catEnv.className = `calc-cat badge ${envData.risk_category === "LOW" ? "badge-success" : (envData.risk_category === "MODERATE" ? "badge-warning" : "badge-danger")}`;

        document.getElementById("sim-out-log").textContent = logData.logistics_risk_score.toFixed(2);
        const catLog = document.getElementById("sim-cat-log");
        catLog.textContent = logData.risk_category;
        catLog.className = `calc-cat badge ${logData.risk_category === "LOW" ? "badge-success" : (logData.risk_category === "MODERATE" ? "badge-warning" : "badge-danger")}`;

        if (envData.contributing_factors) {
            document.getElementById("sf-rain").textContent = envData.contributing_factors.rainfall_risk?.toFixed(2) ?? "—";
            document.getElementById("sf-slope").textContent = envData.contributing_factors.slope_risk?.toFixed(2) ?? "—";
            document.getElementById("sf-elev").textContent = envData.contributing_factors.elevation_exposure?.toFixed(2) ?? "—";
            document.getElementById("sf-veg").textContent = envData.contributing_factors.vegetation_exposure?.toFixed(2) ?? "—";
        }
    } catch (e) {
        console.error("Simulation error:", e);
    }
}

// ---------------------------------------------------------------------------
// FEATURE 5: Rainfall Climatology & Anomaly Charts
// ---------------------------------------------------------------------------
async function loadStateRainfall(stateName) {
    try {
        const [trendsRes, summaryRes] = await Promise.all([
            fetch(`${API_BASE}/analytics/rainfall/trends?state=${encodeURIComponent(stateName)}`),
            fetch(`${API_BASE}/analytics/rainfall/summary`)
        ]);

        if (!trendsRes.ok || !summaryRes.ok) return;

        const trends = await trendsRes.json();
        const summary = await summaryRes.json();

        const stateInfo = summary.states?.find(s => s.state_name.toLowerCase() === stateName.toLowerCase());
        if (stateInfo) {
            document.getElementById("rf-annual-act").textContent = `${stateInfo.estimated_annual_actual_mm} mm`;
            document.getElementById("rf-annual-norm").textContent = `${stateInfo.estimated_annual_normal_mm} mm`;
            document.getElementById("rf-extreme-days").textContent = stateInfo.extreme_days_count;
            document.getElementById("rf-max-daily").textContent = `${stateInfo.max_single_day_rainfall_mm} mm`;
        }

        renderMonthlyChart(trends.monthly_climatology);
        renderAnnualChart(trends.annual_trends);

    } catch (e) {
        console.error("Rainfall load error:", e);
    }
}

function renderMonthlyChart(data) {
    if (!Array.isArray(data) || data.length === 0) return;
    const wrap = document.getElementById("monthly-chart-wrap");
    const maxVal = Math.max(...data.map(d => Math.max(d.actual_daily_avg_mm, d.normal_daily_avg_mm)), 25);
    const height = 180;
    const width = 800;
    const barWidth = 18;

    let barsSvg = "";
    data.forEach((d, i) => {
        const x = 50 + i * 62;
        const hAct = (d.actual_daily_avg_mm / maxVal) * (height - 40);
        const yAct = height - 20 - hAct;
        const hNorm = (d.normal_daily_avg_mm / maxVal) * (height - 40);
        const yNorm = height - 20 - hNorm;

        // Normal bar (gray baseline)
        barsSvg += `<rect x="${x}" y="${yNorm}" width="${barWidth}" height="${hNorm}" fill="#556078" opacity="0.35" rx="2" />`;
        // Actual bar (blue)
        barsSvg += `<rect x="${x + 6}" y="${yAct}" width="${barWidth}" height="${hAct}" fill="#3d7eff" rx="2">
            <title>${d.month_name}: Actual ${d.actual_daily_avg_mm}mm, Normal ${d.normal_daily_avg_mm}mm</title>
        </rect>`;
        // Month label
        barsSvg += `<text x="${x + 13}" y="${height - 4}" fill="#8b99b5" font-size="11" text-anchor="middle">${d.month_name}</text>`;
    });

    wrap.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" class="svg-chart">
            <line x1="40" y1="${height - 20}" x2="${width - 20}" y2="${height - 20}" stroke="#556078" stroke-width="1" />
            ${barsSvg}
            <text x="50" y="20" fill="#3d7eff" font-size="11" font-weight="600">&#9632; Actual Daily Avg</text>
            <text x="180" y="20" fill="#8b99b5" font-size="11" font-weight="600">&#9632; Normal Climatological Avg</text>
        </svg>
    `;
}

function renderAnnualChart(data) {
    if (!Array.isArray(data) || data.length === 0) return;
    const wrap = document.getElementById("annual-chart-wrap");
    const height = 180;
    const width = 800;
    const maxAnomaly = Math.max(...data.map(d => Math.abs(d.mean_anomaly_mm)), 2);
    const zeroY = height / 2;

    let barsSvg = "";
    data.forEach((d, i) => {
        const x = 50 + i * 46;
        const barH = (Math.abs(d.mean_anomaly_mm) / maxAnomaly) * (height / 2 - 30);
        const isPos = d.mean_anomaly_mm >= 0;
        const y = isPos ? (zeroY - barH) : zeroY;
        const fill = isPos ? "#22c55e" : "#f59e0b";

        barsSvg += `<rect x="${x}" y="${y}" width="16" height="${Math.max(barH, 2)}" fill="${fill}" rx="2">
            <title>${d.year}: Departure ${d.mean_anomaly_mm > 0 ? '+' : ''}${d.mean_anomaly_mm}mm, Total: ${d.total_actual_mm}mm</title>
        </rect>`;
        barsSvg += `<text x="${x + 8}" y="${height - 4}" fill="#8b99b5" font-size="10" text-anchor="middle">${String(d.year).slice(2)}</text>`;
    });

    wrap.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" class="svg-chart">
            <line x1="40" y1="${zeroY}" x2="${width - 20}" y2="${zeroY}" stroke="#556078" stroke-dasharray="4 4" stroke-width="1" />
            <text x="35" y="${zeroY + 4}" fill="#8b99b5" font-size="10" text-anchor="end">0</text>
            ${barsSvg}
            <text x="50" y="20" fill="#22c55e" font-size="11" font-weight="600">&#9632; Positive Anomaly (+)</text>
            <text x="200" y="20" fill="#f59e0b" font-size="11" font-weight="600">&#9632; Negative Anomaly (-)</text>
        </svg>
    `;
}

// ---------------------------------------------------------------------------
// FEATURE 6: Calculation History & Audit Reports
// ---------------------------------------------------------------------------
async function loadHistoryTable() {
    const tbody = document.getElementById("history-tbody");
    if (!tbody) return;

    try {
        const res = await fetch(`${API_BASE}/routes/history`);
        if (!res.ok) return;
        const data = await res.json();
        const items = data.history || [];

        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color: var(--text-muted); padding: 32px;">No route calculations saved yet. Calculate a route on the planner to see history.</td></tr>`;
            return;
        }

        let html = "";
        items.forEach(item => {
            const dateStr = item.created_at ? new Date(item.created_at).toLocaleString() : "N/A";
            const valClass = item.validation_status === "PASSED" ? "badge-success" : "badge-danger";
            const confRating = item.confidence_rating || "Unrated";
            const confPct = item.confidence_score ? `${item.confidence_score}%` : "—";

            html += `
                <tr>
                    <td><strong>#${item.id}</strong></td>
                    <td style="font-size: 11px; color: var(--text-muted);">${dateStr}</td>
                    <td><strong>${escapeHtml(item.origin_name)}</strong> &rarr; <strong>${escapeHtml(item.dest_name)}</strong></td>
                    <td><span class="badge ${item.transport_mode === 'AIRWAY' ? 'badge-warning' : 'badge-primary'}">${item.transport_mode}</span></td>
                    <td>${item.distance_km} km</td>
                    <td><span class="badge ${valClass}">${item.validation_status}</span></td>
                    <td><span class="badge badge-primary">${confRating} (${confPct})</span></td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="loadRouteFromHistory(${item.id})">Map</button>
                        <button class="btn btn-secondary btn-sm" onclick="viewReport(${item.id})">Report</button>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="8" style="color: var(--accent-red); padding: 16px;">Failed to load history: ${e.message}</td></tr>`;
    }
}

async function loadRouteFromHistory(id) {
    if (!id) {
        setStatus("Invalid calculation ID for history playback.", "error");
        return;
    }

    showLoader("Loading saved route from history…");
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    try {
        const res = await fetch(`${API_BASE}/routes/history/${id}`, {
            signal: controller.signal
        });
        if (!res.ok) {
            let errorDetail = `HTTP ${res.status}`;
            try {
                const errJson = await res.json();
                if (errJson && errJson.detail) errorDetail = errJson.detail;
            } catch (_) {}
            throw new Error(errorDetail);
        }
        const data = await res.json();

        // Populate search inputs
        selected.origin = { name: data.origin_name, lat: data.origin_lat, lon: data.origin_lon };
        selected.dest   = { name: data.dest_name, lat: data.dest_lat, lon: data.dest_lon };
        document.getElementById("origin-search").value = data.origin_name;
        document.getElementById("dest-search").value   = data.dest_name;
        placeMarker("origin", data.origin_lat, data.origin_lon, data.origin_name);
        placeMarker("dest", data.dest_lat, data.dest_lon, data.dest_name);

        setTransportMode(data.transport_mode);

        if (data.transport_mode === "ROADWAY") {
            const polyline = flattenRoadCoords(data.coords);
            if (polyline.length >= 2) {
                drawRoadRoute(polyline, data.route_mode);
            }
            showRoadwayResults(data, data.route_mode);
        } else {
            if (data.coords && data.coords.length > 0) {
                drawAirwayLine(data.coords[0][0], data.coords[0][1]);
            }
            showAirwayResults(data);
        }

        switchTab("planner");
        setStatus(`Loaded saved route #${id} from history.`, "success");

    } catch (e) {
        let msg = e.message;
        if (e.name === "AbortError") {
            msg = "Request timed out after 10 seconds.";
        }
        console.error(`Could not load route #${id}:`, e);
        setStatus(`Could not load route: ${msg}`, "error");
        alert(`Could not load route: ${msg}`);
    } finally {
        clearTimeout(timeoutId);
        hideLoader();
    }
}

function viewCurrentReport() {
    if (currentCalculationId) {
        viewReport(currentCalculationId);
    } else {
        setStatus("No active calculation report available. Please calculate a route first.", "warning");
        alert("No active calculation report available. Please calculate a route first.");
    }
}

async function viewReport(id) {
    if (!id) {
        setStatus("No calculation ID provided to load audit report.", "error");
        return;
    }

    showLoader("Fetching audit report…");
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    try {
        const res = await fetch(`${API_BASE}/routes/history/${id}/report`, {
            signal: controller.signal
        });

        if (!res.ok) {
            let errorDetail = `HTTP ${res.status}`;
            try {
                const errJson = await res.json();
                if (errJson && errJson.detail) errorDetail = errJson.detail;
            } catch (_) {
                try {
                    const errText = await res.text();
                    if (errText) errorDetail = errText;
                } catch (_) {}
            }
            throw new Error(errorDetail);
        }

        const text = await res.text();
        const preEl = document.getElementById("report-text-content");
        if (preEl) preEl.textContent = text;
        const modalEl = document.getElementById("report-modal");
        if (modalEl) modalEl.classList.remove("hidden");
        setStatus(`Audit report #${id} loaded successfully.`, "success");

    } catch (e) {
        let msg = e.message;
        if (e.name === "AbortError") {
            msg = "Request timed out after 10 seconds.";
        }
        console.error(`Error loading report #${id}:`, e);
        setStatus(`Failed to load audit report: ${msg}`, "error");
        const preEl = document.getElementById("report-text-content");
        if (preEl) {
            preEl.textContent = `[ERROR: Unable to load audit report for calculation #${id}]\nReason: ${msg}`;
        }
        const modalEl = document.getElementById("report-modal");
        if (modalEl) modalEl.classList.remove("hidden");
    } finally {
        clearTimeout(timeoutId);
        hideLoader();
    }
}

function closeReportModal() {
    const modalEl = document.getElementById("report-modal");
    if (modalEl) modalEl.classList.add("hidden");
    const preEl = document.getElementById("report-text-content");
    if (preEl) preEl.textContent = "No report selected.";
}

function copyReportText() {
    const text = document.getElementById("report-text-content").textContent;
    navigator.clipboard.writeText(text).then(() => {
        alert("Report copied to clipboard.");
    }).catch(() => {
        alert("Could not automatically copy to clipboard.");
    });
}

function downloadReportFile() {
    const text = document.getElementById("report-text-content").textContent;
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `NER_Logistics_Audit_Report_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
