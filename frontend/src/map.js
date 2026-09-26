/**
 * IP PULSE - Interactive OpenStreetMap & Leaflet Map Controller
 * Provides dynamic coordinate centering, custom glowing marker, and popup telemetry.
 */

let mapInstance = null;
let currentMarker = null;

function initMap(containerId = 'map', defaultLat = 37.4225, defaultLng = -122.0850, defaultZoom = 12) {
  const container = document.getElementById(containerId);
  if (!container) return null;

  if (mapInstance) {
    mapInstance.remove();
    mapInstance = null;
  }

  // Initialize Leaflet Map
  mapInstance = L.map(containerId, {
    center: [defaultLat, defaultLng],
    zoom: defaultZoom,
    zoomControl: true,
    attributionControl: false,
    scrollWheelZoom: false,
  });

  // OpenStreetMap Tile Layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    subdomains: ['a', 'b', 'c'],
  }).addTo(mapInstance);

  // Add initial marker
  updateMapLocation(defaultLat, defaultLng, 'Target Coordinates Identified', 'OpenStreetMap Tile Marker Active');

  return mapInstance;
}

function updateMapLocation(lat, lng, title = '', subtitle = '') {
  if (!mapInstance) {
    initMap('map', lat || 37.4225, lng || -122.0850);
    return;
  }

  const latNum = parseFloat(lat);
  const lngNum = parseFloat(lng);

  const coordBadge = document.getElementById('map-coordinates-badge');
  const coordText = document.getElementById('map-coordinates-text');

  if (isNaN(latNum) || isNaN(lngNum) || (latNum === 0 && lngNum === 0)) {
    if (coordText) coordText.textContent = 'Coordinates: Unavailable / Private Network';
    mapInstance.setView([20, 0], 2);
    if (currentMarker) {
      mapInstance.removeLayer(currentMarker);
      currentMarker = null;
    }
    return;
  }

  if (coordText) {
    coordText.textContent = `${latNum.toFixed(4)}°, ${lngNum.toFixed(4)}°`;
  }

  // Smooth Fly-To
  mapInstance.flyTo([latNum, lngNum], 13, {
    animate: true,
    duration: 1.2,
  });

  // Remove previous marker
  if (currentMarker) {
    mapInstance.removeLayer(currentMarker);
  }

  // Create Custom Pulsing Cyan Icon
  const customIcon = L.divIcon({
    className: 'pulse-marker-wrapper',
    html: `<div class="pulse-marker-pin"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
    popupAnchor: [0, -10],
  });

  currentMarker = L.marker([latNum, lngNum], { icon: customIcon }).addTo(mapInstance);

  const popupContent = `
    <div style="font-family: 'Inter', sans-serif; font-size: 12px; line-height: 1.4;">
      <div style="font-weight: 600; color: #00d2ff; margin-bottom: 2px;">${escapeHtml(title || 'Target Coordinates')}</div>
      <div style="color: #bbc9cf;">${escapeHtml(subtitle || '')}</div>
      <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #859399; margin-top: 4px;">
        Lat: ${latNum.toFixed(4)} | Lon: ${lngNum.toFixed(4)}
      </div>
    </div>
  `;

  currentMarker.bindPopup(popupContent).openPopup();
}

function resizeMap() {
  if (mapInstance) {
    setTimeout(() => {
      mapInstance.invalidateSize();
    }, 200);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Global exports for Leaflet map integration
window.initMap = initMap;
window.updateMapLocation = updateMapLocation;
window.resizeMap = resizeMap;
