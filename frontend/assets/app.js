/**
 * IP PULSE - Core Application State & REST API Client
 * Manages view routing, asynchronous lookup requests, real-time polling, and UI rendering.
 */

const API_BASE = ''; // Same-origin REST API

let currentTarget = null;
let fieldStudyPollingInterval = null;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initHomeTabs();
  initSearch();
  initMap('map', 37.4225, -122.0850);

  // Check initial system status
  fetchSystemStatus();

  // Run initial lookup for google.com if requested
  performAnalysis('google.com');
});

// ----------------------------------------------------------------------------
// Navigation & View Routing
// ----------------------------------------------------------------------------

function initNavigation() {
  const navLinks = document.querySelectorAll('aside nav a[data-path]');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const path = link.getAttribute('data-path');
      navigateTo(path);
    });
  });
}

function navigateTo(viewName) {
  const views = ['home', 'history', 'field-study', 'analytics'];
  
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) {
      if (v === viewName) {
        el.classList.remove('hidden');
      } else {
        el.classList.add('hidden');
      }
    }
  });

  // Update active sidebar style
  const navLinks = document.querySelectorAll('aside nav a[data-path]');
  navLinks.forEach(link => {
    const p = link.getAttribute('data-path');
    if (p === viewName) {
      link.classList.add('bg-surface-container-high', 'text-primary', 'font-medium');
      link.classList.remove('text-on-surface-variant');
      link.setAttribute('aria-current', 'page');
    } else {
      link.classList.remove('bg-surface-container-high', 'text-primary', 'font-medium');
      link.classList.add('text-on-surface-variant');
      link.removeAttribute('aria-current');
    }
  });

  // Action on tab switch
  if (viewName === 'home') {
    resizeMap();
  } else if (viewName === 'history') {
    loadHistory();
  } else if (viewName === 'field-study') {
    loadFieldStudy();
  } else if (viewName === 'analytics') {
    loadAnalytics();
  }
}

// ----------------------------------------------------------------------------
// Search & Analysis Execution
// ----------------------------------------------------------------------------

function initSearch() {
  const input = document.getElementById('ip-search-input');
  const btn = document.getElementById('analyze-btn');

  if (btn && input) {
    btn.addEventListener('click', () => {
      const q = input.value.trim();
      if (q) performAnalysis(q);
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = input.value.trim();
        if (q) performAnalysis(q);
      }
    });
  }

  // Quick inquiry chips
  window.setQuery = function(q) {
    if (input) {
      input.value = q;
      performAnalysis(q);
    }
  };
}

async function performAnalysis(query) {
  if (!query) return;

  const loadingEl = document.getElementById('analysis-loading');
  const errorEl = document.getElementById('analysis-error');
  const loadingMsg = document.getElementById('loading-message');
  const inputEl = document.getElementById('ip-search-input');

  if (inputEl) inputEl.value = query;
  currentTarget = query;

  if (errorEl) errorEl.classList.add('hidden');
  if (loadingEl) loadingEl.classList.remove('hidden');

  // Progressive loading status feedback
  const messages = [
    'Analyzing website & resolving DNS...',
    'Probing IP infrastructure & ASN telemetry...',
    'Scanning SSL/TLS certificate & security headers...',
    'Evaluating Trust & Risk scoring models...',
  ];
  let msgIdx = 0;
  const msgTimer = setInterval(() => {
    msgIdx = (msgIdx + 1) % messages.length;
    if (loadingMsg) loadingMsg.textContent = messages[msgIdx];
  }, 700);

  try {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target: query }),
    });

    clearInterval(msgTimer);
    if (loadingEl) loadingEl.classList.add('hidden');

    const data = await res.json();

    if (!res.ok || !data.success) {
      showError(data.error || 'Failed to analyze target domain/IP.');
      return;
    }

    renderAnalysisResults(data);
  } catch (err) {
    clearInterval(msgTimer);
    if (loadingEl) loadingEl.classList.add('hidden');
    showError(`Network connection error: ${err.message}`);
  }
}

function showError(msg) {
  const errorEl = document.getElementById('analysis-error');
  const errorText = document.getElementById('error-message-text');
  if (errorText) errorText.textContent = msg;
  if (errorEl) errorEl.classList.remove('hidden');
}

function renderAnalysisResults(data) {
  const b = data.base || {};
  const sec = data.security || {};
  const intel = data.ip_intel || {};
  const risk = data.risk || {};

  // 1. High-Level Telemetry Cards
  setText('summary-location-country', b.country || 'Unknown');
  setText('summary-location-city', `${b.city || 'Unknown'}, ${b.region || ''}`.trim().replace(/^,\s*|,\s*$/g, ''));
  setText('summary-ip-value', b.selected_ip || 'Unavailable');
  setText('summary-ip-details', `${b.ip_version || 'IPv4'} • ${intel.infrastructure_type || 'Standard Routing'}`);
  setText('summary-org-name', b.organization || b.isp || 'Unknown');
  setText('summary-asn-badge', b.asn ? `ASN: ${b.asn}` : 'ASN: Unknown');
  setText('summary-infra-type', intel.infrastructure_type || 'Cloud / Datacenter');
  setText('summary-threat-status', intel.vpn_status === 'DETECTED' ? 'VPN Detected' : (intel.tor_status === 'DETECTED' ? 'Tor Node' : 'Direct IP'));

  // 2. Dual Trust & Risk Gauges
  const trustScore = typeof risk.trust_score === 'number' ? risk.trust_score : 50;
  const riskScore = typeof risk.risk_score === 'number' ? risk.risk_score : 50;

  setText('trust-score-val', trustScore);
  setText('risk-score-val', riskScore);
  setText('trust-score-tier', risk.confidence_rating ? `Tier: ${risk.confidence_rating}` : 'Confidence: Analytical');
  setText('risk-score-category', risk.risk_category || 'MODERATE');

  // Update Trust Gauge Bar
  const trustBar = document.getElementById('trust-score-bar');
  if (trustBar) trustBar.style.width = `${Math.min(Math.max(trustScore, 0), 100)}%`;

  const riskBar = document.getElementById('risk-score-bar');
  if (riskBar) riskBar.style.width = `${Math.min(Math.max(riskScore, 0), 100)}%`;

  // Render Factor Badges
  renderFactorBadges('trust-factors-container', risk.positive_factors || [], 'border-tertiary/30 text-tertiary');
  renderFactorBadges('risk-factors-container', risk.risk_factors || [], 'border-error/30 text-error');

  // 3. Leaflet Map Update
  if (b.latitude && b.longitude) {
    updateMapLocation(b.latitude, b.longitude, b.input || data.target, `${b.city || ''}, ${b.country || ''}`);
  } else {
    updateMapLocation(null, null);
  }

  // 4. Tab 1: Network Details
  setText('net-domain', b.normalized_input || b.input || 'N/A');
  setText('net-ip', b.selected_ip || 'N/A');
  setText('net-version', b.ip_version || 'N/A');
  setText('net-dns-time', `${b.dns_response_time_ms ? b.dns_response_time_ms.toFixed(1) : '0.0'} ms`);
  setText('net-api-time', `${b.api_response_time_ms ? b.api_response_time_ms.toFixed(1) : '0.0'} ms`);
  setText('net-total-time', `${b.total_response_time_ms ? b.total_response_time_ms.toFixed(1) : '0.0'} ms`);
  setText('net-country', b.country || 'N/A');
  setText('net-region', b.region || 'N/A');
  setText('net-city', b.city || 'N/A');
  setText('net-timezone', b.timezone || 'N/A');
  setText('net-asn', b.asn || 'N/A');
  setText('net-isp', b.isp || 'N/A');
  setText('net-org', b.organization || 'N/A');
  setText('net-dns-status', b.dns_status || 'N/A');
  setText('net-geo-status', b.geolocation_status || 'N/A');

  // 5. Tab 2: Security Intelligence
  setText('sec-target', sec.target_domain || b.normalized_input || 'N/A');
  setBooleanBadge('sec-https-badge', sec.is_https, 'HTTPS Enforced', 'HTTP Only');
  setBooleanBadge('sec-tls-badge', sec.tls_valid, 'Certificate Valid', 'Invalid Certificate');
  setText('sec-tls-version', sec.tls_version || 'Not Detected');
  setText('sec-cipher', sec.cipher_name || 'Not Detected');
  setText('sec-expiry', sec.expires_in_days !== null && sec.expires_in_days !== undefined ? `${sec.expires_in_days} days` : 'Unknown');
  setText('sec-issuer', sec.issuer_org || 'Unknown');
  setBooleanBadge('sec-hsts', sec.hsts_header, 'Enabled', 'Not Detected');
  setBooleanBadge('sec-csp', sec.csp_header, 'Enabled', 'Not Detected');
  setBooleanBadge('sec-xframe', sec.x_frame_options, 'Enabled', 'Not Detected');
  setText('sec-redirects', sec.redirect_count !== undefined ? String(sec.redirect_count) : '0');
  setText('sec-final-url', sec.final_url || 'N/A');

  // 6. Tab 3: IP Infrastructure & Anonymizer
  setText('intel-ip', intel.ip_address || b.selected_ip || 'N/A');
  setText('intel-infra-type', intel.infrastructure_type || 'Unknown');
  setStatusBadge('intel-vpn-badge', intel.vpn_status);
  setStatusBadge('intel-proxy-badge', intel.proxy_status);
  setStatusBadge('intel-tor-badge', intel.tor_status);
  setStatusBadge('intel-dc-badge', intel.datacenter_status);

  // 7. Tab 4: AI Explanation & Provenance
  setText('ai-personality-text', data.personality || 'IP personality summary unavailable.');
  setText('ai-explanation-text', data.explanation || 'Evidence explanation unavailable.');
  
  // Render Provenance Timeline
  renderProvenanceTimeline(data.provenance || []);
}

function renderFactorBadges(containerId, factors, colorClasses) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  if (!factors || factors.length === 0) {
    container.innerHTML = `<span class="text-[11px] text-outline">None identified</span>`;
    return;
  }
  factors.forEach(f => {
    const chip = document.createElement('span');
    chip.className = `px-2 py-0.5 rounded text-[11px] font-label-data-md border ${colorClasses}`;
    chip.textContent = f;
    container.appendChild(chip);
  });
}

function renderProvenanceTimeline(records) {
  const container = document.getElementById('provenance-timeline');
  if (!container) return;
  container.innerHTML = '';

  if (!records || records.length === 0) {
    container.innerHTML = `<div class="text-outline text-[12px]">Provenance records not available.</div>`;
    return;
  }

  records.forEach((p, idx) => {
    const item = document.createElement('div');
    item.className = 'flex items-start gap-space-sm relative pb-3';
    item.innerHTML = `
      <div class="w-2 h-2 rounded-full bg-primary mt-1.5 flex-shrink-0"></div>
      <div class="flex flex-col min-w-0">
        <div class="flex items-center gap-2">
          <span class="font-headline-sm text-[13px] text-on-surface font-medium">${escapeHtml(p.stage)}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-surface-container font-label-data-md text-outline">${escapeHtml(p.source)}</span>
          <span class="text-[10px] text-tertiary font-label-data-md">${escapeHtml(p.status)}</span>
        </div>
        <div class="text-[11px] text-on-surface-variant mt-0.5">${escapeHtml(p.details)}</div>
      </div>
    `;
    container.appendChild(item);
  });
}

function setBooleanBadge(elementId, val, trueText, falseText) {
  const el = document.getElementById(elementId);
  if (!el) return;
  if (val === true) {
    el.textContent = trueText;
    el.className = 'px-2 py-0.5 rounded text-[11px] font-label-data-md bg-tertiary/10 text-tertiary border border-tertiary/30';
  } else if (val === false) {
    el.textContent = falseText;
    el.className = 'px-2 py-0.5 rounded text-[11px] font-label-data-md bg-error/10 text-error border border-error/30';
  } else {
    el.textContent = 'Unknown';
    el.className = 'px-2 py-0.5 rounded text-[11px] font-label-data-md bg-surface-container text-outline border border-outline-variant';
  }
}

function setStatusBadge(elementId, status) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const s = String(status || '').toUpperCase();
  if (s === 'DETECTED') {
    el.textContent = 'DETECTED';
    el.className = 'px-2 py-0.5 rounded text-[11px] font-label-data-md bg-error/15 text-error border border-error/40';
  } else if (s === 'NOT_DETECTED') {
    el.textContent = 'NOT DETECTED';
    el.className = 'px-2 py-0.5 rounded text-[11px] font-label-data-md bg-tertiary/15 text-tertiary border border-tertiary/40';
  } else {
    el.textContent = 'UNKNOWN';
    el.className = 'px-2 py-0.5 rounded text-[11px] font-label-data-md bg-surface-container text-outline border border-outline-variant';
  }
}

// ----------------------------------------------------------------------------
// Home Sub-Tabs (Network / Security / IP Intel / AI Report)
// ----------------------------------------------------------------------------

function initHomeTabs() {
  const tabs = ['network', 'security', 'ipintel', 'aireport'];

  window.switchHomeTab = function(tabName) {
    tabs.forEach(t => {
      const content = document.getElementById(`tab-content-${t}`);
      const btn = document.getElementById(`tab-btn-${t}`);
      const indicator = document.getElementById(`tab-indicator-${t}`);

      if (t === tabName) {
        if (content) content.classList.remove('hidden');
        if (btn) {
          btn.classList.add('text-on-surface');
          btn.classList.remove('text-on-surface-variant');
        }
        if (indicator) indicator.classList.remove('hidden');
      } else {
        if (content) content.classList.add('hidden');
        if (btn) {
          btn.classList.remove('text-on-surface');
          btn.classList.add('text-on-surface-variant');
        }
        if (indicator) indicator.classList.add('hidden');
      }
    });
  };
}

// ----------------------------------------------------------------------------
// History View Management
// ----------------------------------------------------------------------------

async function loadHistory() {
  const tableBody = document.getElementById('history-table-body');
  const totalCountEl = document.getElementById('history-total-count');
  const searchInput = document.getElementById('history-search-input');

  if (tableBody) {
    tableBody.innerHTML = `<tr><td colspan="7" class="py-space-lg text-center text-outline">Loading audit ledger from database...</td></tr>`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/history`);
    const data = await res.json();

    if (!res.ok || !data.success) {
      if (tableBody) tableBody.innerHTML = `<tr><td colspan="7" class="py-space-lg text-center text-error">Failed to load history: ${data.error}</td></tr>`;
      return;
    }

    const records = data.records || [];
    if (totalCountEl) totalCountEl.textContent = records.length;

    renderHistoryTable(records);

    // Bind real-time search filter
    if (searchInput) {
      searchInput.oninput = () => {
        const query = searchInput.value.toLowerCase().trim();
        const filtered = records.filter(r => 
          (r.domain && r.domain.toLowerCase().includes(query)) ||
          (r.ip_address && r.ip_address.toLowerCase().includes(query)) ||
          (r.country && r.country.toLowerCase().includes(query))
        );
        renderHistoryTable(filtered);
      };
    }
  } catch (err) {
    if (tableBody) tableBody.innerHTML = `<tr><td colspan="7" class="py-space-lg text-center text-error">Connection error: ${err.message}</td></tr>`;
  }
}

function renderHistoryTable(records) {
  const tableBody = document.getElementById('history-table-body');
  if (!tableBody) return;

  if (records.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="7" class="py-space-xl text-center text-outline">No stored observations in database.</td></tr>`;
    return;
  }

  tableBody.innerHTML = '';
  records.forEach(r => {
    const tr = document.createElement('tr');
    tr.className = 'group hover:bg-surface-container/70 transition-colors border-b border-surface-container';

    // Format ISO timestamp
    let formattedDate = r.timestamp || 'N/A';
    try {
      if (r.timestamp) {
        const dt = new Date(r.timestamp);
        formattedDate = dt.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
      }
    } catch (e) {}

    const isSuccess = r.status === 'SUCCESS';
    const statusBadge = isSuccess
      ? `<span class="px-2 py-0.5 rounded text-[11px] font-label-data-md bg-tertiary/15 text-tertiary border border-tertiary/30">SUCCESS</span>`
      : `<span class="px-2 py-0.5 rounded text-[11px] font-label-data-md bg-error/15 text-error border border-error/30">${escapeHtml(r.status || 'FAILED')}</span>`;

    tr.innerHTML = `
      <td class="py-space-md px-space-lg font-label-data-md text-outline text-[12px]">${escapeHtml(formattedDate)}</td>
      <td class="py-space-md px-space-lg font-medium text-on-surface">${escapeHtml(r.domain || r.input_value || 'Unknown')}</td>
      <td class="py-space-md px-space-lg font-label-data-md text-primary">${escapeHtml(r.ip_address || 'Unavailable')}</td>
      <td class="py-space-md px-space-lg text-[13px] text-on-surface-variant">${escapeHtml(`${r.city || ''}, ${r.country || ''}`.trim().replace(/^,\s*|,\s*$/g, '') || 'Unknown')}</td>
      <td class="py-space-md px-space-lg text-[12px] text-outline truncate max-w-[150px]">${escapeHtml(r.organization || r.isp || 'N/A')}</td>
      <td class="py-space-md px-space-lg">${statusBadge}</td>
      <td class="py-space-md px-space-lg text-right">
        <div class="flex items-center justify-end gap-2">
          <button class="px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-primary hover:text-white text-[12px] font-label-data-md transition-all cursor-pointer" onclick="inspectFromHistory('${escapeHtml(r.domain || r.input_value)}')">
            Inspect
          </button>
          <button class="p-1 rounded text-outline hover:text-error hover:bg-surface-container-high transition-colors" onclick="deleteHistoryItem(${r.id})" title="Delete record">
            <span class="material-symbols-outlined text-[16px]">delete</span>
          </button>
        </div>
      </td>
    `;
    tableBody.appendChild(tr);
  });
}

window.inspectFromHistory = function(target) {
  navigateTo('home');
  performAnalysis(target);
};

window.deleteHistoryItem = async function(id) {
  if (!confirm(`Delete history record #${id}?`)) return;
  try {
    const res = await fetch(`${API_BASE}/api/history/${id}`, { method: 'DELETE' });
    if (res.ok) {
      loadHistory();
    }
  } catch (err) {
    alert(`Could not delete record: ${err.message}`);
  }
};

window.clearAllHistory = async function() {
  if (!confirm('Are you sure you want to clear all history records? This cannot be undone.')) return;
  try {
    const res = await fetch(`${API_BASE}/api/history`, { method: 'DELETE' });
    if (res.ok) {
      loadHistory();
    }
  } catch (err) {
    alert(`Could not clear history: ${err.message}`);
  }
};

// ----------------------------------------------------------------------------
// Field Study View Management
// ----------------------------------------------------------------------------

async function loadFieldStudy() {
  try {
    const res = await fetch(`${API_BASE}/api/field-study`);
    const data = await res.json();

    if (!res.ok || !data.success) {
      return;
    }

    const avail = data.available_count || 0;
    const target = data.target || 50;
    const rem = data.remaining || 0;
    const pct = data.progress_percentage || 0;

    setText('field-study-count', avail);
    setText('field-study-target', `/ ${target}`);
    setText('field-study-summary-count', avail);
    setText('field-study-remaining-text', `${rem} observations remaining`);
    setText('field-study-pct-text', `${pct}% of target sample quota completed`);

    const bar = document.getElementById('field-study-progress-bar');
    if (bar) bar.style.width = `${pct}%`;

    renderFieldStudyTable(data.records || []);
  } catch (err) {
    console.error('Field study fetch error:', err);
  }
}

function renderFieldStudyTable(records) {
  const tableBody = document.getElementById('field-study-table-body');
  if (!tableBody) return;

  if (records.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="6" class="py-space-xl text-center text-outline">No field study observations recorded yet. Perform manual lookups from Home to populate.</td></tr>`;
    return;
  }

  tableBody.innerHTML = '';
  records.forEach(r => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-surface-container/70 transition-colors border-b border-surface-container';

    tr.innerHTML = `
      <td class="py-space-md px-space-lg font-label-data-md text-outline">${r.test_id}</td>
      <td class="py-space-md px-space-lg font-medium text-on-surface">${escapeHtml(r.domain)}</td>
      <td class="py-space-md px-space-lg text-[12px] font-label-data-md text-outline">${escapeHtml(r.category || 'General')}</td>
      <td class="py-space-md px-space-lg font-label-data-md text-primary">${escapeHtml(r.ip_address)}</td>
      <td class="py-space-md px-space-lg text-[13px] text-on-surface-variant">${escapeHtml(`${r.city || ''}, ${r.country || ''}`.trim().replace(/^,\s*|,\s*$/g, '') || 'Unknown')}</td>
      <td class="py-space-md px-space-lg">
        <span class="px-2 py-0.5 rounded text-[11px] font-label-data-md bg-tertiary/15 text-tertiary border border-tertiary/30">
          RECORDED
        </span>
      </td>
    `;
    tableBody.appendChild(tr);
  });
}

// Modal handling for optional auto-complete
window.openAutoCompleteModal = function() {
  const modal = document.getElementById('autocomplete-modal');
  if (modal) modal.classList.remove('hidden');
};

window.closeAutoCompleteModal = function() {
  const modal = document.getElementById('autocomplete-modal');
  if (modal) modal.classList.add('hidden');
};

window.confirmAutoComplete = async function() {
  closeAutoCompleteModal();
  const banner = document.getElementById('field-study-running-banner');
  if (banner) banner.classList.remove('hidden');

  try {
    const res = await fetch(`${API_BASE}/api/field-study/complete-remaining`, { method: 'POST' });
    if (res.ok) {
      // Poll progress every 2 seconds
      if (fieldStudyPollingInterval) clearInterval(fieldStudyPollingInterval);
      fieldStudyPollingInterval = setInterval(async () => {
        await loadFieldStudy();
        const count = parseInt(document.getElementById('field-study-count')?.textContent || '0', 10);
        if (count >= 50) {
          clearInterval(fieldStudyPollingInterval);
          if (banner) banner.classList.add('hidden');
        }
      }, 2000);
    }
  } catch (err) {
    if (banner) banner.classList.add('hidden');
    alert(`Could not complete field study: ${err.message}`);
  }
};

// ----------------------------------------------------------------------------
// Analytics View Management
// ----------------------------------------------------------------------------

async function loadAnalytics() {
  const container = document.getElementById('analytics-content');
  const emptyBanner = document.getElementById('analytics-empty');

  try {
    const res = await fetch(`${API_BASE}/api/analytics`);
    const data = await res.json();

    if (!res.ok || !data.success || data.insufficient_data) {
      if (container) container.classList.add('hidden');
      if (emptyBanner) emptyBanner.classList.remove('hidden');
      return;
    }

    if (container) container.classList.remove('hidden');
    if (emptyBanner) emptyBanner.classList.add('hidden');

    setText('analytics-n-count', `N = ${data.total_observations} Inspected Endpoints`);
    setText('analytics-dns-avg', `${data.mean_dns_time_ms} ms`);
    setText('analytics-api-avg', `${data.mean_api_time_ms} ms`);
    setText('analytics-ipv4-count', data.ipv4_count);
    setText('analytics-ipv6-count', data.ipv6_count);

    // Render Trust Brackets Histogram
    const brackets = data.trust_brackets || [];
    brackets.forEach((b, idx) => {
      const bar = document.getElementById(`histogram-bar-${idx}`);
      const countEl = document.getElementById(`histogram-count-${idx}`);
      if (bar) bar.style.height = `${Math.max(b.pct, 5)}%`;
      if (countEl) countEl.textContent = b.count;
    });

    // Render Top Countries List
    const countryList = document.getElementById('analytics-top-countries');
    if (countryList) {
      countryList.innerHTML = '';
      (data.top_countries || []).forEach(c => {
        const row = document.createElement('div');
        row.className = 'flex items-center justify-between py-1.5 border-b border-surface-container text-sm';
        row.innerHTML = `
          <span class="text-on-surface font-medium">${escapeHtml(c.country)}</span>
          <span class="font-label-data-md text-primary">${c.count} (${c.pct}%)</span>
        `;
        countryList.appendChild(row);
      });
    }

    // Render Top Organizations List
    const orgList = document.getElementById('analytics-top-orgs');
    if (orgList) {
      orgList.innerHTML = '';
      (data.top_organizations || []).forEach(o => {
        const row = document.createElement('div');
        row.className = 'flex items-center justify-between py-1.5 border-b border-surface-container text-sm';
        row.innerHTML = `
          <span class="text-on-surface truncate max-w-[220px]">${escapeHtml(o.org)}</span>
          <span class="font-label-data-md text-secondary">${o.count}</span>
        `;
        orgList.appendChild(row);
      });
    }
  } catch (err) {
    console.error('Analytics fetch error:', err);
  }
}

// ----------------------------------------------------------------------------
// Utilities
// ----------------------------------------------------------------------------

async function fetchSystemStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    const data = await res.json();
    if (data.status === 'operational') {
      const badge = document.getElementById('system-status-badge');
      if (badge) badge.textContent = 'System Online';
    }
  } catch (e) {}
}

function setText(elementId, text) {
  const el = document.getElementById(elementId);
  if (el) el.textContent = text !== null && text !== undefined ? String(text) : 'N/A';
}

function copyValue(val) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(val);
    const toast = document.getElementById('copy-toast');
    if (toast) {
      toast.classList.remove('opacity-0');
      setTimeout(() => toast.classList.add('opacity-0'), 1800);
    }
  }
}

window.copyValue = copyValue;
