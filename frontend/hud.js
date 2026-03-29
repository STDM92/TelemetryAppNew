/// <reference path="./telemetry-types.js" />

let socket = null;

/**
 * Cached DOM references.
 */
const ui = {
    status: document.getElementById("status"),
    speed: document.getElementById("speed"),
    throttle: document.getElementById("throttle"),
    brake: document.getElementById("brake"),
    trackCars: document.getElementById("track-cars"),
};

/**
 * Updates the connection status text and color.
 * @param {string} text
 * @param {string} color
 */
function setStatus(text, color) {
    ui.status.innerText = text;
    ui.status.style.color = color;
}

/**
 * Sets a bar width in percent.
 * @param {HTMLElement|null} element
 * @param {number|null|undefined} ratio
 */
function setBarWidth(element, ratio) {
    if (!element) return;
    const percent = (ratio ?? 0) * 100;
    element.style.width = `${percent}%`;
}

const SVG_NS = "http://www.w3.org/2000/svg";

/**
 * Removes all child nodes from an element.
 * @param {Element|null} element
 */
function clearElement(element) {
    if (!element) return;
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

/**
 * Converts lap ratio (0..1) to a point on the circular track map.
 * Top of circle = start/finish.
 *
 * @param {number} lapRatio
 * @returns {{x: number, y: number}}
 */
function lapRatioToTrackPoint(lapRatio) {
    const centerX = 150;
    const centerY = 150;
    const radius = 110;

    // Start at top, rotate clockwise
    const angle = (lapRatio * Math.PI * 2) - (Math.PI / 2);

    return {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
    };
}

/**
 * Renders the simple circular track map.
 * Player car = green
 * Other cars = grey
 *
 * @param {UnifiedSnapshot} snapshot
 */
function updateTrackMap(snapshot) {
    if (!ui.trackCars) return;

    clearElement(ui.trackCars);

    const trackMap = snapshot.track_map;
    const cars = trackMap?.cars;

    if (!cars || !Array.isArray(cars)) {
        return;
    }

    const playerCarIndex = trackMap.player_car_index;

    for (const car of cars) {
        const lapRatio = car?.lap_distance_ratio;

        if (lapRatio == null) {
            continue;
        }

        const point = lapRatioToTrackPoint(lapRatio);
        const isPlayer = car.car_index === playerCarIndex;

        const dot = document.createElementNS(SVG_NS, "circle");
        dot.setAttribute("cx", point.x.toFixed(2));
        dot.setAttribute("cy", point.y.toFixed(2));
        dot.setAttribute("r", isPlayer ? "6" : "4");
        dot.setAttribute("fill", isPlayer ? "#00ff00" : "#888888");
        dot.setAttribute("stroke", isPlayer ? "#ffffff" : "none");
        dot.setAttribute("stroke-width", isPlayer ? "1.5" : "0");

        ui.trackCars.appendChild(dot);
    }
}

/**
 * Updates speed display.
 * @param {UnifiedSnapshot} snapshot
 */
function updateSpeed(snapshot) {
    const speedKph = snapshot.powertrain?.vehicle_speed_kph;
    if (speedKph != null) {
        ui.speed.innerText = speedKph.toFixed(0);
    }
}

/**
 * Updates throttle and brake bars.
 * @param {UnifiedSnapshot} snapshot
 */
function updateInputs(snapshot) {
    setBarWidth(ui.throttle, snapshot.inputs?.throttle_ratio);
    setBarWidth(ui.brake, snapshot.inputs?.brake_ratio);
}

/**
 * Applies one telemetry snapshot to the HUD.
 * @param {UnifiedSnapshot} snapshot
 */
function renderSnapshot(snapshot) {
    updateSpeed(snapshot);
    updateInputs(snapshot);
    updateTrackMap(snapshot);
}

/**
 * Handles one incoming websocket message.
 * @param {MessageEvent<string>} event
 */
function handleMessage(event) {
    /** @type {UnifiedSnapshot} */
    const snapshot = JSON.parse(event.data);
    renderSnapshot(snapshot);
}


function buildWebSocketUrl() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    return `${protocol}//${host}/ws`;
}

/**
 * Opens the websocket connection and wires up lifecycle callbacks.
 */
function connectSocket() {
    const wsUrl = buildWebSocketUrl();
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        setStatus("Connected", "#00ff00");
    };

    socket.onmessage = (event) => {
        handleMessage(event);
    };

    socket.onclose = () => {
        setStatus("Disconnected", "#ff0000");
    };

    socket.onerror = () => {
        setStatus("Connection error", "#ff9900");
    };
}
/**
 * Page startup.
 */
function initializeHud() {
    setStatus("Connecting...", "#ffffff");
    connectSocket();
}

initializeHud();