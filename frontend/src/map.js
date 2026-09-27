/**
 * IP PULSE - Interactive OpenStreetMap & Leaflet Map Controller
 * Provides dynamic coordinate centering, custom glowing marker, and popup telemetry.
 */

import { escapeHtml } from './utils.js';

let mapInstance = null;
let currentMarker = null;

function isValidLatLng(lat, lng) {
  const latNum = parseFloat(lat);
  const lngNum = parseFloat(lng);
  return (
    Number.isFinite(latNum) &&
    Number.isFinite(lngNum) &&
    latNum >= -90 &&
    latNum <= 90 &&
    lngNum >= -180 &&
    lngNum <= 180 &&
    !(latNum === 0 && lngNum === 0)
  );
}

function initMap(containerId = 'map', defaultLat = 37.4225, defaultLng = -122.0850, defaultZoom = 12) {
  const container = document.getElementById(containerId);
  if (!container) return null;

  if (mapInstance) {
    try {
      mapInstance.remove();
    } catch (_) {}
    mapInstance = null;
    currentMarker = null;
  }

  const latNum = parseFloat(defaultLat);
  const lngNum = parseFloat(defaultLng);
  const initialLat = Number.isFinite(latNum) && latNum >= -90 && latNum <= 90 ? latNum : 37.4225;
  const initialLng = Number.isFinite(lngNum) && lngNum >= -180 && lngNum <= 180 ? lngNum : -122.0850;

  try {
    // Initialize Leaflet Map
    mapInstance = L.map(containerId, {
      center: [initialLat, initialLng],
      zoom: defaultZoom,
      zoomControl: true,
      attributionControl: true,
      scrollWheelZoom: false,
    });

    // OpenStreetMap Tile Layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      subdomains: ['a', 'b', 'c'],
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
    }).addTo(mapInstance);

    // Place initial marker immediately without flyTo animation (prevents zero-size division and NaN LatLng)
    updateMapLocation(initialLat, initialLng, 'Target Coordinates Identified', 'OpenStreetMap Tile Marker Active', false);

    // Schedule container size recalculation once DOM layout settles
    setTimeout(() => {
      if (mapInstance) {
        try {
          mapInstance.invalidateSize();
        } catch (_) {}
      }
    }, 200);
  } catch (mapInitErr) {
    console.error('Error initializing Leaflet map:', mapInitErr);
  }

  return mapInstance;
}

function updateMapLocation(lat, lng, title = '', subtitle = '', animate = true) {
  const latNum = parseFloat(lat);
  const lngNum = parseFloat(lng);

  const coordBadge = document.getElementById('map-coordinates-badge');
  const coordText = document.getElementById('map-coordinates-text');

  // Strict coordinate boundary and validity validation
  if (!isValidLatLng(latNum, lngNum)) {
    if (coordText) coordText.textContent = 'Coordinates: Unavailable / Private Network';
    if (mapInstance) {
      try {
        mapInstance.setView([20, 0], 2);
      } catch (_) {}
      if (currentMarker) {
        try {
          mapInstance.removeLayer(currentMarker);
        } catch (_) {}
        currentMarker = null;
      }
    }
    return;
  }

  if (!mapInstance) {
    initMap('map', latNum, lngNum);
    return;
  }

  if (coordText) {
    coordText.textContent = `${latNum.toFixed(4)}°, ${lngNum.toFixed(4)}°`;
  }

  // Check if map container has calculated non-zero dimensions before attempting flyTo
  let hasValidDimensions = false;
  try {
    const size = mapInstance.getSize();
    hasValidDimensions = Boolean(size && size.x > 0 && size.y > 0);
  } catch (_) {
    hasValidDimensions = false;
  }

  if (animate && hasValidDimensions) {
    try {
      mapInstance.flyTo([latNum, lngNum], 13, {
        animate: true,
        duration: 1.2,
      });
    } catch (flyErr) {
      console.warn('Map flyTo animation failed, using setView fallback:', flyErr);
      try {
        mapInstance.setView([latNum, lngNum], 13);
      } catch (_) {}
    }
  } else {
    try {
      mapInstance.setView([latNum, lngNum], 13);
    } catch (_) {}
  }

  // Remove previous marker safely
  if (currentMarker) {
    try {
      mapInstance.removeLayer(currentMarker);
    } catch (_) {}
    currentMarker = null;
  }

  try {
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
  } catch (markerErr) {
    console.warn('Failed to place marker on Leaflet map:', markerErr);
  }
}

let resizeTimer = null;
function resizeMap() {
  if (mapInstance) {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      resizeTimer = null;
      if (mapInstance) {
        mapInstance.invalidateSize();
      }
    }, 100);
  }
}

// Global & ES Module exports for Leaflet map integration
window.initMap = initMap;
window.updateMapLocation = updateMapLocation;
window.resizeMap = resizeMap;

export { initMap, updateMapLocation, resizeMap };
