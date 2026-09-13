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
        el.classList.remove('page-view-section');
        void el.offsetWidth;
        el.classList.add('page-view-section');
      } else {
        el.classList.add('hidden');
      }
    }
  });

  // Update active sidebar style with smooth transition
  const navLinks = document.querySelectorAll('aside nav a[data-path]');
  navLinks.forEach(link => {
    const p = link.getAttribute('data-path');
    if (p === viewName) {
      link.classList.add('sidebar-link-active', 'font-medium');
      link.classList.remove('text-on-surface-variant');
      link.setAttribute('aria-current', 'page');
    } else {
      link.classList.remove('sidebar-link-active', 'font-medium');
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

  // Store latest result globally for Explainability Modal
  window.currentAnalysisResult = data;
  const trustData = risk.trust || {};
  const ipRiskData = risk.ip_risk || {};

  // 2. Dual Trust & Risk Gauges
  const trustScore = typeof risk.trust_score === 'number' ? risk.trust_score : (typeof trustData.score === 'number' ? trustData.score : 50);
  const riskScore = typeof risk.risk_score === 'number' ? risk.risk_score : (typeof ipRiskData.score === 'number' ? ipRiskData.score : 5);

  setText('trust-score-val', trustScore);
  setText('risk-score-val', riskScore);

  // Confidence & Classification Badges
  const trustConfidence = trustData.confidence || risk.confidence_rating || 'HIGH';
  setText('trust-score-tier', `Confidence: ${trustConfidence}`);
  
  const trustClass = trustData.classification || (trustScore >= 80 ? 'LIKELY SAFE' : (trustScore >= 60 ? 'GENERALLY SAFE' : (trustScore >= 40 ? 'REVIEW RECOMMENDED' : (trustScore >= 20 ? 'SUSPICIOUS' : 'HIGH RISK'))));
  setText('trust-classification-badge', trustClass);
  setText('trust-evidence-coverage', `Evidence: ${trustData.evidence_coverage || '7/8'} signals`);

  const riskClass = ipRiskData.classification || risk.risk_category || (riskScore <= 19 ? 'LOW RISK' : (riskScore <= 39 ? 'MODERATE' : (riskScore <= 59 ? 'ELEVATED' : (riskScore <= 79 ? 'HIGH RISK' : 'CRITICAL'))));
  setText('risk-score-category', riskClass);
  setText('risk-classification-badge', riskClass);
  setText('risk-evidence-coverage', `Evidence: ${ipRiskData.evidence_coverage || '5/5'} signals`);

  // Update Trust Gauge Bar with smooth transition
  const trustBar = document.getElementById('trust-score-bar');
  if (trustBar) {
    trustBar.style.width = '0%';
    setTimeout(() => {
      trustBar.style.width = `${Math.min(Math.max(trustScore, 0), 100)}%`;
    }, 40);
  }

  // Update Risk Gauge Bar with semantic risk colors and smooth transition
  const riskBar = document.getElementById('risk-score-bar');
  if (riskBar) {
    riskBar.style.width = '0%';
    riskBar.classList.remove('risk-gauge-low', 'risk-gauge-moderate', 'risk-gauge-high');
    if (riskScore <= 20) {
      riskBar.classList.add('risk-gauge-low');
    } else if (riskScore <= 59) {
      riskBar.classList.add('risk-gauge-moderate');
    } else {
      riskBar.classList.add('risk-gauge-high');
    }
    setTimeout(() => {
      riskBar.style.width = `${Math.min(Math.max(riskScore, 0), 100)}%`;
    }, 40);
  }

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

  // 8. Phase 18: Render Intelligence Provenance Chain & IP Personality
  renderIntelligenceChain(data.intelligence_chain, b, intel);
  renderIPPersonality(data.ip_personality, data.personality);

  // 9. Phase 19: Set current target for Field Study curation
  const currentTarget = data.target || b.input || b.domain || b.selected_ip || '';
  window.currentAnalysisTarget = currentTarget;
  const targetBadge = document.getElementById('active-target-badge');
  if (targetBadge) {
    targetBadge.textContent = currentTarget || 'Current Target';
  }
  const addBtn = document.getElementById('btn-add-to-field-study');
  if (addBtn) {
    addBtn.disabled = false;
    addBtn.innerHTML = `
      <span class="material-symbols-outlined text-[16px]">biotech</span>
      <span>Add to Field Study</span>
    `;
    addBtn.className = 'px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high border border-surface-container text-xs font-mono text-on-surface flex items-center gap-1.5 transition-all cursor-pointer shadow-sm hover:border-primary/40';
  }
}

function renderIntelligenceChain(chain, base, intel) {
  if (!chain) {
    chain = {
      domain: base.input || 'Direct IP Target',
      ip: base.selected_ip || 'Unknown',
      asn: base.asn || intel.asn || 'Unknown',
      organization: base.organization || intel.organization || 'Unknown',
      infrastructure: intel.infrastructure_type || 'Unknown',
      location: `${base.city || ''}, ${base.country || ''}`.trim().replace(/^,\s*/, '') || 'Unknown Location'
    };
  }

  // Node 1: Domain
  const isDirectIp = base.input_type === 'IPV4' || base.input_type === 'IPV6' || (base.input && /^\d+\.\d+\.\d+\.\d+$/.test(base.input));
  const domainVal = isDirectIp ? 'Direct IP Target' : (chain.domain || base.input || 'Unknown');
  setText('chain-node-domain', domainVal);
  const domainStatusEl = document.getElementById('chain-status-domain');
  if (domainStatusEl) {
    domainStatusEl.textContent = isDirectIp ? 'DIRECT' : (domainVal !== 'Unknown' ? 'RESOLVED' : 'UNKNOWN');
    domainStatusEl.className = isDirectIp
      ? 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-surface-container text-outline border border-surface-container'
      : 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-primary/10 text-primary border border-primary/20';
  }

  // Node 2: IP Address
  const ipVal = chain.ip || base.selected_ip || 'Unknown';
  setText('chain-node-ip', ipVal);
  const ipStatusEl = document.getElementById('chain-status-ip');
  if (ipStatusEl) {
    ipStatusEl.textContent = ipVal !== 'Unknown' ? 'RESOLVED' : 'UNKNOWN';
    ipStatusEl.className = ipVal !== 'Unknown'
      ? 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-primary/10 text-primary border border-primary/20'
      : 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-error/10 text-error border border-error/20';
  }

  // Node 3: ASN
  const asnVal = chain.asn || base.asn || intel.asn || 'Unknown';
  setText('chain-node-asn', asnVal);
  const asnStatusEl = document.getElementById('chain-status-asn');
  if (asnStatusEl) {
    asnStatusEl.textContent = (asnVal && asnVal !== 'Unknown' && asnVal !== 'N/A') ? 'ASSIGNED' : 'UNASSIGNED';
    asnStatusEl.className = (asnVal && asnVal !== 'Unknown' && asnVal !== 'N/A')
      ? 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-secondary/10 text-secondary border border-secondary/20'
      : 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-surface-container text-outline border border-surface-container';
  }

  // Node 4: Organization
  const orgVal = chain.organization || base.organization || intel.organization || base.isp || 'Unknown';
  setText('chain-node-org', orgVal);
  const orgStatusEl = document.getElementById('chain-status-org');
  if (orgStatusEl) {
    orgStatusEl.textContent = (orgVal && orgVal !== 'Unknown' && orgVal !== 'N/A') ? 'IDENTIFIED' : 'UNKNOWN';
    orgStatusEl.className = (orgVal && orgVal !== 'Unknown' && orgVal !== 'N/A')
      ? 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-secondary/10 text-secondary border border-secondary/20'
      : 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-surface-container text-outline border border-surface-container';
  }

  // Node 5: Infrastructure
  const infraVal = chain.infrastructure || intel.infrastructure_type || 'Unknown';
  setText('chain-node-infra', infraVal);
  const infraStatusEl = document.getElementById('chain-status-infra');
  if (infraStatusEl) {
    infraStatusEl.textContent = (infraVal && infraVal !== 'Unknown' && infraVal !== 'N/A') ? 'CLASSIFIED' : 'UNCLASSIFIED';
    infraStatusEl.className = (infraVal && infraVal !== 'Unknown' && infraVal !== 'N/A')
      ? 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-tertiary/10 text-tertiary border border-tertiary/20'
      : 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-surface-container text-outline border border-surface-container';
  }

  // Node 6: Location
  const locVal = chain.location || [base.city, base.country].filter(Boolean).join(', ') || 'Unknown Location';
  setText('chain-node-loc', locVal);
  const locStatusEl = document.getElementById('chain-status-loc');
  if (locStatusEl) {
    locStatusEl.textContent = (locVal && locVal !== 'Unknown Location') ? 'GEOLOCATED' : 'UNKNOWN';
    locStatusEl.className = (locVal && locVal !== 'Unknown Location')
      ? 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-primary/10 text-primary border border-primary/20'
      : 'text-[9px] font-mono px-1.5 py-0.2 rounded bg-surface-container text-outline border border-surface-container';
  }

  // Staggered animation trigger
  const nodes = document.querySelectorAll('#intel-chain-container .chain-node');
  nodes.forEach((n, idx) => {
    n.classList.remove('chain-node-animate');
    void n.offsetWidth;
    n.style.setProperty('--node-idx', idx);
    n.classList.add('chain-node-animate');
  });
}

function renderIPPersonality(personality, fallbackSummary) {
  const summary = personality?.summary || fallbackSummary || 'IP personality unavailable.';
  setText('personality-summary-text', summary);

  const conf = personality?.confidence || 'HIGH';
  const confEl = document.getElementById('personality-confidence-badge');
  if (confEl) {
    confEl.textContent = `CONFIDENCE: ${conf}`;
    confEl.className = conf === 'HIGH'
      ? 'text-[10px] font-mono px-2 py-0.2 rounded-full bg-primary/10 text-primary border border-primary/20'
      : (conf === 'MEDIUM'
        ? 'text-[10px] font-mono px-2 py-0.2 rounded-full bg-tertiary/10 text-tertiary border border-tertiary/20'
        : 'text-[10px] font-mono px-2 py-0.2 rounded-full bg-surface-container text-outline border border-surface-container');
  }

  const container = document.getElementById('personality-badges-container');
  if (!container) return;
  container.innerHTML = '';

  const labels = personality?.labels || ['INFRASTRUCTURE UNCLASSIFIED'];

  const iconMap = {
    'CLOUD HOSTED': '☁',
    'DATACENTER INFRASTRUCTURE': '🏢',
    'CDN EDGE NODE': '⚡',
    'GLOBAL NETWORK': '🌐',
    'REGIONAL OPERATOR': '📡',
    'RESIDENTIAL NETWORK': '🏠',
    'MOBILE NETWORK': '📱',
    'ENTERPRISE NETWORK': '🏛',
    'ACADEMIC / RESEARCH': '🎓',
    'GOVERNMENT NETWORK': '⚖',
    'LOW ANONYMIZATION': '🛡',
    'TOR ASSOCIATED': '🧅',
    'PROXY ASSOCIATED': '🔀',
    'VPN ASSOCIATED': '🔒',
    'IPV6 NATIVE': '🔢',
    'INFRASTRUCTURE UNCLASSIFIED': '❓',
  };

  const colorMap = {
    'TOR ASSOCIATED': 'border-error/40 text-error bg-error/10',
    'PROXY ASSOCIATED': 'border-secondary/40 text-secondary bg-secondary/10',
    'VPN ASSOCIATED': 'border-secondary/40 text-secondary bg-secondary/10',
    'LOW ANONYMIZATION': 'border-tertiary/40 text-tertiary bg-tertiary/10',
    'CDN EDGE NODE': 'border-primary/40 text-primary bg-primary/10',
    'CLOUD HOSTED': 'border-primary/40 text-primary bg-primary/10',
    'GLOBAL NETWORK': 'border-primary/40 text-primary bg-primary/10',
    'DATACENTER INFRASTRUCTURE': 'border-secondary/40 text-secondary bg-secondary/10',
    'RESIDENTIAL NETWORK': 'border-tertiary/40 text-tertiary bg-tertiary/10',
    'MOBILE NETWORK': 'border-tertiary/40 text-tertiary bg-tertiary/10',
    'IPV6 NATIVE': 'border-primary/40 text-primary bg-primary/10',
  };

  labels.forEach(label => {
    const icon = iconMap[label] || '🏷';
    const color = colorMap[label] || 'border-surface-container text-outline bg-surface-container/40';
    const badge = document.createElement('span');
    badge.className = `personality-badge px-2.5 py-1 rounded-lg text-xs font-mono font-medium border flex items-center gap-1.5 shadow-sm ${color}`;
    badge.innerHTML = `<span>${icon}</span> <span>${label}</span>`;
    container.appendChild(badge);
  });
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

      if (t === tabName) {
        if (content) {
          content.classList.remove('hidden');
          content.classList.remove('page-view-section');
          void content.offsetWidth;
          content.classList.add('page-view-section');
        }
        if (btn) {
          btn.classList.add('text-on-surface', 'intel-tab-btn-active');
          btn.classList.remove('text-on-surface-variant');
        }
      } else {
        if (content) content.classList.add('hidden');
        if (btn) {
          btn.classList.remove('text-on-surface', 'intel-tab-btn-active');
          btn.classList.add('text-on-surface-variant');
        }
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
    tr.className = 'data-table-row group hover:bg-surface-container/70 transition-colors border-b border-surface-container/60';

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
// Field Study View Management (Phase 19)
// ----------------------------------------------------------------------------

window.addToFieldStudy = async function() {
  const target = window.currentAnalysisTarget;
  if (!target) {
    alert('No active website target to add to the Field Study.');
    return;
  }

  const btn = document.getElementById('btn-add-to-field-study');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `
      <span class="material-symbols-outlined text-[16px] animate-spin">refresh</span>
      <span>Adding...</span>
    `;
  }

  try {
    const res = await fetch(`${API_BASE}/api/field-study/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target: target })
    });
    const data = await res.json();

    if (res.ok && data.success) {
      if (btn) {
        btn.innerHTML = `
          <span class="material-symbols-outlined text-[16px] text-emerald-400">check_circle</span>
          <span class="text-emerald-400 font-semibold">Added to Field Study</span>
        `;
        btn.className = 'px-3 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-xs font-mono text-emerald-400 flex items-center gap-1.5 transition-all cursor-default';
      }
    } else if (res.status === 409 || data.duplicate) {
      if (btn) {
        btn.innerHTML = `
          <span class="material-symbols-outlined text-[16px] text-secondary">verified</span>
          <span class="text-secondary">Already in Field Study</span>
        `;
        btn.className = 'px-3 py-1.5 rounded-lg bg-secondary/10 border border-secondary/30 text-xs font-mono text-secondary flex items-center gap-1.5 transition-all cursor-default';
      }
      alert(data.message || `Domain '${target}' is already recorded in the 50-Site Field Study.`);
    } else {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `
          <span class="material-symbols-outlined text-[16px]">biotech</span>
          <span>Add to Field Study</span>
        `;
        btn.className = 'px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high border border-surface-container text-xs font-mono text-on-surface flex items-center gap-1.5 transition-all cursor-pointer shadow-sm hover:border-primary/40';
      }
      alert(data.message || data.error || 'Failed to add observation to Field Study.');
    }
  } catch (err) {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `
        <span class="material-symbols-outlined text-[16px]">biotech</span>
        <span>Add to Field Study</span>
      `;
    }
    alert(`Could not add to field study: ${err.message}`);
  }
};

async function loadFieldStudy() {
  try {
    const res = await fetch(`${API_BASE}/api/field-study`);
    const data = await res.json();

    if (!res.ok || !data.success) {
      return;
    }

    const avail = data.available_count || 0;
    const target = data.target || 50;
    const rem = data.remaining !== undefined ? data.remaining : Math.max(target - avail, 0);
    const pct = data.progress_percentage !== undefined ? data.progress_percentage : Math.round((avail / target) * 100);
    const isReached = avail >= target || data.status === 'TARGET_REACHED';

    setText('field-study-count', avail);
    setText('field-study-target', `/ ${target}`);
    setText('field-study-pct-text', `${pct}% of target quota completed`);
    setText('field-study-remaining-text', isReached ? 'Target sample quota fulfilled' : `${rem} observations remaining`);

    const statusBadge = document.getElementById('field-study-status-badge');
    if (statusBadge) {
      if (isReached) {
        statusBadge.textContent = 'TARGET REACHED';
        statusBadge.className = 'ml-3 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40';
      } else {
        statusBadge.textContent = `${pct}% COMPLETE`;
        statusBadge.className = 'ml-3 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-primary/10 text-primary border border-primary/30';
      }
    }

    const bar = document.getElementById('field-study-progress-bar');
    if (bar) bar.style.width = `${Math.min(pct, 100)}%`;

    // Disable auto-complete if target already reached
    const autoBtn = document.getElementById('btn-auto-complete');
    if (autoBtn) {
      if (isReached) {
        autoBtn.disabled = true;
        autoBtn.classList.add('opacity-60', 'cursor-not-allowed');
        autoBtn.innerHTML = `
          <span class="material-symbols-outlined text-[16px]">check_circle</span>
          <span>Target Reached (50/50)</span>
        `;
      } else {
        autoBtn.disabled = false;
        autoBtn.classList.remove('opacity-60', 'cursor-not-allowed');
        autoBtn.innerHTML = `
          <span class="material-symbols-outlined text-[16px]">autorenew</span>
          <span>Complete Remaining (${rem})</span>
        `;
      }
    }

    // Render 4 Summary Cards & Secondary Telemetry
    renderFieldStudySummary(data.summary || {}, avail, target);

    // Cache records and render table
    window.currentFieldStudyRecords = data.records || [];
    renderFieldStudyTable(window.currentFieldStudyRecords);
  } catch (err) {
    console.error('Field study fetch error:', err);
  }
}

function renderFieldStudySummary(summary, avail, target) {
  // 1. Websites Tested Card
  setText('fs-summary-websites', avail);
  setText('fs-summary-status-text', avail >= target ? 'Target quota fulfilled' : 'Sample collection active');

  // 2. HTTPS Adoption Card
  const httpsPct = typeof summary.https_adoption_pct === 'number' ? summary.https_adoption_pct : 0.0;
  setText('fs-summary-https', `${httpsPct.toFixed(1)}%`);

  // 3. Average Trust Score Card
  const avgTrust = typeof summary.avg_trust_score === 'number' ? summary.avg_trust_score : 0.0;
  setText('fs-summary-trust', avgTrust.toFixed(1));
  const trustTier = avgTrust >= 80 ? 'Likely Safe (Sample mean)' : (avgTrust >= 60 ? 'Generally Safe (Sample mean)' : (avgTrust >= 40 ? 'Moderate Trust' : 'Review Recommended'));
  setText('fs-summary-trust-tier', trustTier);

  // 4. Average IP Risk Card
  const avgRisk = typeof summary.avg_risk_score === 'number' ? summary.avg_risk_score : 0.0;
  setText('fs-summary-risk', avgRisk.toFixed(1));
  const riskTier = avgRisk <= 20 ? 'Low Risk (Sample mean)' : (avgRisk <= 40 ? 'Moderate Risk' : (avgRisk <= 60 ? 'Elevated Risk' : 'High Risk'));
  setText('fs-summary-risk-tier', riskTier);

  // Secondary Telemetry Strip
  const commonInfra = summary.most_common_infrastructure || 'Unknown';
  setText('fs-summary-infra', commonInfra);
  setText('fs-summary-vpn', summary.vpn_detections || 0);
  setText('fs-summary-proxy', summary.proxy_detections || 0);
  setText('fs-summary-tor', summary.tor_detections || 0);
}

function renderFieldStudyTable(records) {
  const tableBody = document.getElementById('field-study-table-body');
  if (!tableBody) return;

  if (!records || records.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="9" class="py-12 text-center text-outline font-mono">No field study observations recorded yet. Look up domains on Home and click "Add to Field Study" to curate observations.</td></tr>`;
    return;
  }

  tableBody.innerHTML = '';
  records.forEach((r, idx) => {
    const tr = document.createElement('tr');
    tr.className = 'cursor-pointer hover:bg-surface-container/60 transition-colors border-b border-surface-container/50 group';
    tr.onclick = () => openFieldStudyDetail(r.id || r.test_id);

    // Trust badge color
    const trustVal = r.website_trust_score !== null && r.website_trust_score !== undefined ? Math.round(r.website_trust_score) : null;
    let trustBadgeClass = 'bg-surface-container text-outline';
    if (trustVal !== null) {
      if (trustVal >= 80) trustBadgeClass = 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30';
      else if (trustVal >= 50) trustBadgeClass = 'bg-primary/15 text-primary border border-primary/30';
      else trustBadgeClass = 'bg-amber-500/15 text-amber-400 border border-amber-500/30';
    }

    // Risk badge color
    const riskVal = r.ip_risk_score !== null && r.ip_risk_score !== undefined ? Math.round(r.ip_risk_score) : null;
    let riskBadgeClass = 'bg-surface-container text-outline';
    if (riskVal !== null) {
      if (riskVal <= 20) riskBadgeClass = 'bg-secondary/15 text-secondary border border-secondary/30';
      else if (riskVal <= 50) riskBadgeClass = 'bg-amber-500/15 text-amber-400 border border-amber-500/30';
      else riskBadgeClass = 'bg-red-500/15 text-red-400 border border-red-500/30';
    }

    // HTTPS badge color
    const isHttps = r.https_status === 'Enabled' || r.https_status === 'Active' || r.https_status === 'SUCCESS';
    const httpsBadgeClass = isHttps
      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
      : (r.https_status === 'Disabled' ? 'bg-red-500/15 text-red-400 border border-red-500/30' : 'bg-surface-container text-outline');

    // Format date nicely
    let formattedDate = 'Recent';
    if (r.observed_at) {
      try {
        const d = new Date(r.observed_at);
        formattedDate = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
      } catch (e) {
        formattedDate = r.observed_at.substring(0, 16);
      }
    }

    tr.innerHTML = `
      <td class="py-3 px-3 text-center font-mono text-outline">${r.test_id || (idx + 1)}</td>
      <td class="py-3 px-4 font-mono font-medium text-on-surface group-hover:text-primary transition-colors">
        <div class="flex items-center gap-1.5">
          <span class="material-symbols-outlined text-[15px] text-primary">public</span>
          <span class="truncate max-w-[160px]">${escapeHtml(r.domain)}</span>
        </div>
      </td>
      <td class="py-3 px-4 font-mono text-primary truncate max-w-[140px]">${escapeHtml(r.resolved_ip || r.ip_address || 'Unknown')}</td>
      <td class="py-3 px-4 text-on-surface-variant truncate max-w-[110px]">${escapeHtml(r.country || 'Unknown')}</td>
      <td class="py-3 px-4 font-mono text-outline truncate max-w-[130px]">${escapeHtml(r.infrastructure_type || 'Unknown')}</td>
      <td class="py-3 px-3 text-center">
        <span class="px-2 py-0.5 rounded text-[10px] font-mono ${httpsBadgeClass}">
          ${escapeHtml(r.https_status || 'Unknown')}
        </span>
      </td>
      <td class="py-3 px-3 text-center">
        <span class="px-2 py-0.5 rounded text-[11px] font-mono font-semibold ${trustBadgeClass}">
          ${trustVal !== null ? trustVal : '—'}
        </span>
      </td>
      <td class="py-3 px-3 text-center">
        <span class="px-2 py-0.5 rounded text-[11px] font-mono font-semibold ${riskBadgeClass}">
          ${riskVal !== null ? riskVal : '—'}
        </span>
      </td>
      <td class="py-3 px-4 text-right font-mono text-[11px] text-outline whitespace-nowrap">
        ${formattedDate}
      </td>
    `;
    tableBody.appendChild(tr);
  });
}

window.openFieldStudyDetail = function(obsId) {
  const records = window.currentFieldStudyRecords || [];
  const obs = records.find(r => (r.id == obsId || r.test_id == obsId));
  if (!obs) {
    console.warn(`Observation #${obsId} not found in current cache.`);
    return;
  }

  // Header
  setText('modal-obs-test-id', `#${obs.test_id || 1}`);
  setText('modal-obs-domain', obs.domain);
  setText('modal-obs-category', obs.category || 'General Web');
  setText('modal-obs-timestamp', `Observed: ${obs.observed_at || 'Unknown'}`);

  // Body: 5 organized cards
  const bodyEl = document.getElementById('modal-obs-body');
  if (bodyEl) {
    const coords = (obs.latitude !== null && obs.latitude !== undefined && obs.longitude !== null && obs.longitude !== undefined)
      ? `${obs.latitude}, ${obs.longitude}` : 'Unknown';

    bodyEl.innerHTML = `
      <!-- Section 1: Target & IP Identity -->
      <div class="p-3.5 rounded-xl bg-surface-container-lowest/80 border border-surface-container flex flex-col gap-2">
        <div class="flex items-center gap-1.5 text-primary text-[11px] font-semibold uppercase tracking-wider">
          <span class="material-symbols-outlined text-[15px]">badge</span>
          <span>Target Identity</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">Domain:</span>
          <span class="text-on-surface font-semibold truncate">${escapeHtml(obs.domain)}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">Resolved IP:</span>
          <span class="text-primary font-bold">${escapeHtml(obs.resolved_ip || obs.ip_address || 'Unknown')}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">IP Version:</span>
          <span class="text-on-surface">${escapeHtml(obs.ip_version || 'IPv4')}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">Category:</span>
          <span class="text-on-surface">${escapeHtml(obs.category || 'General Web')}</span>
        </div>
        <div class="flex justify-between py-1">
          <span class="text-outline">Observation Status:</span>
          <span class="text-emerald-400 font-semibold">${escapeHtml(obs.observation_status || 'RECORDED')}</span>
        </div>
      </div>

      <!-- Section 2: Geolocation -->
      <div class="p-3.5 rounded-xl bg-surface-container-lowest/80 border border-surface-container flex flex-col gap-2">
        <div class="flex items-center gap-1.5 text-primary text-[11px] font-semibold uppercase tracking-wider">
          <span class="material-symbols-outlined text-[15px]">location_on</span>
          <span>Geolocation Telemetry</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">Country:</span>
          <span class="text-on-surface">${escapeHtml(obs.country || 'Unknown')} ${obs.country_code ? `(${escapeHtml(obs.country_code)})` : ''}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">Region / State:</span>
          <span class="text-on-surface">${escapeHtml(obs.region || 'Unknown')}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">City:</span>
          <span class="text-on-surface">${escapeHtml(obs.city || 'Unknown')}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">Coordinates:</span>
          <span class="text-on-surface font-mono">${escapeHtml(coords)}</span>
        </div>
        <div class="flex justify-between py-1">
          <span class="text-outline">Confidence:</span>
          <span class="text-secondary font-semibold">${escapeHtml(obs.geolocation_confidence || 'HIGH')}</span>
        </div>
      </div>

      <!-- Section 3: Network & Infrastructure -->
      <div class="p-3.5 rounded-xl bg-surface-container-lowest/80 border border-surface-container flex flex-col gap-2">
        <div class="flex items-center gap-1.5 text-tertiary text-[11px] font-semibold uppercase tracking-wider">
          <span class="material-symbols-outlined text-[15px]">hub</span>
          <span>Network & Infrastructure</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">ASN:</span>
          <span class="text-on-surface font-semibold">${escapeHtml(obs.asn || 'Unknown')}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">Organization:</span>
          <span class="text-on-surface truncate max-w-[200px]">${escapeHtml(obs.organization || 'Unknown')}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">ISP:</span>
          <span class="text-on-surface truncate max-w-[200px]">${escapeHtml(obs.isp || 'Unknown')}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">Network Type:</span>
          <span class="text-on-surface">${escapeHtml(obs.network_type || 'Unknown')}</span>
        </div>
        <div class="flex justify-between py-1">
          <span class="text-outline">Infrastructure:</span>
          <span class="text-primary font-semibold">${escapeHtml(obs.infrastructure_type || 'Unknown')}</span>
        </div>
      </div>

      <!-- Section 4: Security Intelligence -->
      <div class="p-3.5 rounded-xl bg-surface-container-lowest/80 border border-surface-container flex flex-col gap-2">
        <div class="flex items-center gap-1.5 text-tertiary text-[11px] font-semibold uppercase tracking-wider">
          <span class="material-symbols-outlined text-[15px]">security</span>
          <span>Security Intelligence</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">HTTPS Status:</span>
          <span class="${obs.https_status === 'Enabled' ? 'text-emerald-400 font-semibold' : 'text-outline'}">${escapeHtml(obs.https_status || 'Unknown')}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">TLS / SSL:</span>
          <span class="${obs.tls_status === 'Valid' ? 'text-emerald-400' : 'text-outline'}">${escapeHtml(obs.tls_status || 'Unknown')}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">VPN Detection:</span>
          <span class="${obs.vpn_status === 'DETECTED' ? 'text-amber-400 font-bold' : 'text-on-surface'}">${escapeHtml(obs.vpn_status || 'NOT_DETECTED')}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">Proxy Detection:</span>
          <span class="${obs.proxy_status === 'DETECTED' ? 'text-amber-400 font-bold' : 'text-on-surface'}">${escapeHtml(obs.proxy_status || 'NOT_DETECTED')}</span>
        </div>
        <div class="flex justify-between py-1">
          <span class="text-outline">Tor Exit Node:</span>
          <span class="${obs.tor_status === 'DETECTED' ? 'text-red-400 font-bold' : 'text-on-surface'}">${escapeHtml(obs.tor_status || 'NOT_DETECTED')}</span>
        </div>
      </div>

      <!-- Section 5: Scores & Performance (Spans 2 cols) -->
      <div class="md:col-span-2 p-3.5 rounded-xl bg-surface-container-lowest/80 border border-surface-container flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5 text-primary text-[11px] font-semibold uppercase tracking-wider">
            <span class="material-symbols-outlined text-[15px]">speed</span>
            <span>Deterministic Scoring & Latency Telemetry</span>
          </div>
          <span class="text-[11px] text-outline">Evidence Coverage: ${Math.round((obs.evidence_coverage || 0) * 100)}%</span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
          <div class="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container flex flex-col">
            <span class="text-[10px] text-outline uppercase">Trust Score</span>
            <span class="text-lg font-bold text-primary">${obs.website_trust_score !== null && obs.website_trust_score !== undefined ? obs.website_trust_score : 'N/A'}<span class="text-xs text-outline font-normal">/100</span></span>
            <span class="text-[10px] text-on-surface-variant truncate">${escapeHtml(obs.website_trust_classification || 'Unknown')}</span>
          </div>
          <div class="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container flex flex-col">
            <span class="text-[10px] text-outline uppercase">IP Risk Score</span>
            <span class="text-lg font-bold text-secondary">${obs.ip_risk_score !== null && obs.ip_risk_score !== undefined ? obs.ip_risk_score : 'N/A'}<span class="text-xs text-outline font-normal">/100</span></span>
            <span class="text-[10px] text-on-surface-variant truncate">${escapeHtml(obs.ip_risk_classification || 'Unknown')}</span>
          </div>
          <div class="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container flex flex-col">
            <span class="text-[10px] text-outline uppercase">DNS Latency</span>
            <span class="text-lg font-bold text-on-surface">${obs.dns_response_time_ms ? obs.dns_response_time_ms + ' ms' : 'N/A'}</span>
            <span class="text-[10px] text-outline">Lookup time</span>
          </div>
          <div class="p-2.5 rounded-lg bg-surface-container/60 border border-surface-container flex flex-col">
            <span class="text-[10px] text-outline uppercase">Score Confidence</span>
            <span class="text-lg font-bold text-emerald-400">${escapeHtml(obs.score_confidence || 'HIGH')}</span>
            <span class="text-[10px] text-outline">Deterministic rating</span>
          </div>
        </div>
      </div>
    `;
  }

  const modal = document.getElementById('field-study-detail-modal');
  if (modal) modal.classList.remove('hidden');
};

window.closeFieldStudyDetail = function() {
  const modal = document.getElementById('field-study-detail-modal');
  if (modal) modal.classList.add('hidden');
};

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

    if (!res.ok || !data.success || data.insufficient_data || !data.overview || data.overview.total_observations === 0) {
      if (container) container.classList.add('hidden');
      if (emptyBanner) emptyBanner.classList.remove('hidden');
      return;
    }

    if (container) container.classList.remove('hidden');
    if (emptyBanner) emptyBanner.classList.add('hidden');

    const ov = data.overview;
    const total = ov.total_observations;

    // ------------------------------------------------------------------------
    // SECTION 1: Field Study Overview
    // ------------------------------------------------------------------------
    setText('ov-sample-size', `${total} / ${ov.sample_target || 50}`);
    setText(
      'ov-remaining-text',
      ov.target_reached
        ? 'Target quota (50/50) complete'
        : `${ov.remaining_to_target} remaining to target quota`
    );
    setText(
      'ov-progress-summary-text',
      `${total} / ${ov.sample_target || 50} collected (${ov.collection_progress_pct}%)`
    );
    const progressBar = document.getElementById('analytics-progress-bar');
    if (progressBar) progressBar.style.width = `${Math.min(ov.collection_progress_pct, 100)}%`;

    setText(
      'ov-https-pct',
      ov.https_adoption_pct !== null ? `${ov.https_adoption_pct}%` : 'N/A'
    );
    const sec = data.security_analysis || {};
    const httpsEnabled = sec.https_status ? sec.https_status.enabled : 0;
    setText('ov-https-detail', `${httpsEnabled} of ${total} endpoints encrypted`);

    setText(
      'ov-avg-trust',
      ov.mean_trust_score !== null ? ov.mean_trust_score.toFixed(1) : '—'
    );
    setText(
      'ov-avg-risk',
      ov.mean_risk_score !== null ? ov.mean_risk_score.toFixed(1) : '—'
    );

    // ------------------------------------------------------------------------
    // SECTION 2: Trust & Risk Score Analysis (Dual Histograms)
    // ------------------------------------------------------------------------
    const trust = data.trust_analysis || {};
    setText('trust-min-val', trust.min !== null && trust.min !== undefined ? trust.min : '—');
    setText('trust-avg-val', trust.mean !== null && trust.mean !== undefined ? trust.mean.toFixed(1) : '—');
    setText('trust-max-val', trust.max !== null && trust.max !== undefined ? trust.max : '—');

    (trust.histogram || []).forEach((b, idx) => {
      const bar = document.getElementById(`trust-bar-${idx}`);
      const countEl = document.getElementById(`trust-bar-count-${idx}`);
      if (bar) bar.style.height = `${Math.max(b.pct, 4)}%`;
      if (countEl) countEl.textContent = `${b.count} (${b.pct}%)`;
    });

    const trustClassList = document.getElementById('trust-classifications-list');
    if (trustClassList) {
      trustClassList.innerHTML = '';
      (trust.classifications || []).forEach(c => {
        const pill = document.createElement('div');
        pill.className = 'px-2.5 py-1 rounded-md bg-surface-container-low border border-surface-container flex items-center gap-1.5 text-xs';
        pill.innerHTML = `
          <span class="text-on-surface-variant font-medium">${escapeHtml(c.classification)}:</span>
          <span class="text-primary font-bold">${c.count}</span>
          <span class="text-outline">(${c.pct}%)</span>
        `;
        trustClassList.appendChild(pill);
      });
    }

    const risk = data.risk_analysis || {};
    setText('risk-min-val', risk.min !== null && risk.min !== undefined ? risk.min : '—');
    setText('risk-avg-val', risk.mean !== null && risk.mean !== undefined ? risk.mean.toFixed(1) : '—');
    setText('risk-max-val', risk.max !== null && risk.max !== undefined ? risk.max : '—');

    (risk.histogram || []).forEach((b, idx) => {
      const bar = document.getElementById(`risk-bar-${idx}`);
      const countEl = document.getElementById(`risk-bar-count-${idx}`);
      if (bar) bar.style.height = `${Math.max(b.pct, 4)}%`;
      if (countEl) countEl.textContent = `${b.count} (${b.pct}%)`;
    });

    const riskClassList = document.getElementById('risk-classifications-list');
    if (riskClassList) {
      riskClassList.innerHTML = '';
      (risk.classifications || []).forEach(c => {
        const pill = document.createElement('div');
        pill.className = 'px-2.5 py-1 rounded-md bg-surface-container-low border border-surface-container flex items-center gap-1.5 text-xs';
        pill.innerHTML = `
          <span class="text-on-surface-variant font-medium">${escapeHtml(c.classification)}:</span>
          <span class="text-secondary font-bold">${c.count}</span>
          <span class="text-outline">(${c.pct}%)</span>
        `;
        riskClassList.appendChild(pill);
      });
    }

    // ------------------------------------------------------------------------
    // SECTION 3: Security & Transport Encryption
    // ------------------------------------------------------------------------
    const httpsStatus = sec.https_status || { enabled: 0, disabled: 0, unknown: 0, adoption_pct: 0 };
    const httpsAdoptPct = httpsStatus.adoption_pct !== null ? `${httpsStatus.adoption_pct}%` : 'N/A';
    setText('sec-https-rate-badge', `${httpsAdoptPct} ADOPTED`);
    setText('sec-https-enabled-val', httpsStatus.enabled);
    setText('sec-https-enabled-pct', total > 0 ? `${(httpsStatus.enabled / total * 100).toFixed(1)}%` : '0%');
    setText('sec-https-disabled-val', httpsStatus.disabled);
    setText('sec-https-disabled-pct', total > 0 ? `${(httpsStatus.disabled / total * 100).toFixed(1)}%` : '0%');
    setText('sec-https-unknown-val', httpsStatus.unknown);
    setText('sec-https-unknown-pct', total > 0 ? `${(httpsStatus.unknown / total * 100).toFixed(1)}%` : '0%');

    const barHttpsEnabled = document.getElementById('sec-bar-https-enabled');
    const barHttpsDisabled = document.getElementById('sec-bar-https-disabled');
    const barHttpsUnknown = document.getElementById('sec-bar-https-unknown');
    if (barHttpsEnabled) barHttpsEnabled.style.width = total > 0 ? `${(httpsStatus.enabled / total * 100).toFixed(1)}%` : '0%';
    if (barHttpsDisabled) barHttpsDisabled.style.width = total > 0 ? `${(httpsStatus.disabled / total * 100).toFixed(1)}%` : '0%';
    if (barHttpsUnknown) barHttpsUnknown.style.width = total > 0 ? `${(httpsStatus.unknown / total * 100).toFixed(1)}%` : '0%';

    const tlsStatus = sec.tls_status || { valid: 0, invalid_or_expired: 0, unknown: 0, valid_pct: 0 };
    const tlsValidPct = tlsStatus.valid_pct !== null ? `${tlsStatus.valid_pct}%` : 'N/A';
    setText('sec-tls-rate-badge', `${tlsValidPct} VALID`);
    setText('sec-tls-valid-val', tlsStatus.valid);
    setText('sec-tls-valid-pct', total > 0 ? `${(tlsStatus.valid / total * 100).toFixed(1)}%` : '0%');
    setText('sec-tls-invalid-val', tlsStatus.invalid_or_expired);
    setText('sec-tls-invalid-pct', total > 0 ? `${(tlsStatus.invalid_or_expired / total * 100).toFixed(1)}%` : '0%');
    setText('sec-tls-unknown-val', tlsStatus.unknown);
    setText('sec-tls-unknown-pct', total > 0 ? `${(tlsStatus.unknown / total * 100).toFixed(1)}%` : '0%');

    const barTlsValid = document.getElementById('sec-bar-tls-valid');
    const barTlsInvalid = document.getElementById('sec-bar-tls-invalid');
    const barTlsUnknown = document.getElementById('sec-bar-tls-unknown');
    if (barTlsValid) barTlsValid.style.width = total > 0 ? `${(tlsStatus.valid / total * 100).toFixed(1)}%` : '0%';
    if (barTlsInvalid) barTlsInvalid.style.width = total > 0 ? `${(tlsStatus.invalid_or_expired / total * 100).toFixed(1)}%` : '0%';
    if (barTlsUnknown) barTlsUnknown.style.width = total > 0 ? `${(tlsStatus.unknown / total * 100).toFixed(1)}%` : '0%';

    // ------------------------------------------------------------------------
    // SECTION 4: Infrastructure & Network Analysis
    // ------------------------------------------------------------------------
    const net = data.network_analysis || {};
    const ipVers = net.ip_versions || { ipv4: 0, ipv6: 0, ipv4_pct: 0, ipv6_pct: 0 };
    setText('analytics-ipv4-count', ipVers.ipv4);
    setText('analytics-ipv4-pct', `${ipVers.ipv4_pct}%`);
    setText('analytics-ipv6-count', ipVers.ipv6);
    setText('analytics-ipv6-pct', `${ipVers.ipv6_pct}%`);

    const latency = net.query_latency || { mean_dns_ms: 0, mean_api_ms: 0 };
    setText('analytics-dns-avg', `${latency.mean_dns_ms.toFixed(1)} ms`);
    setText('analytics-api-avg', `${latency.mean_api_ms.toFixed(1)} ms`);

    const infra = net.infrastructure || { cloud_datacenter: 0, traditional_other: 0, cloud_pct: 0 };
    setText('infra-cloud-pct-val', `${infra.cloud_pct}% (${infra.cloud_datacenter} hosts)`);
    const infraCloudBar = document.getElementById('infra-cloud-bar');
    if (infraCloudBar) infraCloudBar.style.width = `${infra.cloud_pct}%`;

    const threats = net.threat_indicators || { vpn: 0, proxy: 0, tor: 0 };
    setText('threat-vpn-count', threats.vpn);
    setText('threat-proxy-count', threats.proxy);
    setText('threat-tor-count', threats.tor);

    // ------------------------------------------------------------------------
    // SECTION 5: Country & Autonomous System Distribution
    // ------------------------------------------------------------------------
    const geoAsn = data.geographic_and_asn_distribution || {};
    const countryList = document.getElementById('analytics-top-countries');
    if (countryList) {
      countryList.innerHTML = '';
      const countries = geoAsn.top_countries || data.top_countries || [];
      if (countries.length === 0) {
        countryList.innerHTML = '<div class="py-3 text-xs text-outline font-mono">No geographic data recorded.</div>';
      } else {
        countries.forEach(c => {
          const row = document.createElement('div');
          row.className = 'flex items-center justify-between py-2 border-b border-surface-container/60 text-xs font-mono';
          row.innerHTML = `
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-[15px] text-outline">location_on</span>
              <span class="text-on-surface font-medium">${escapeHtml(c.country)}</span>
            </div>
            <span class="text-primary font-bold">${c.count} <span class="text-outline font-normal">(${c.pct}%)</span></span>
          `;
          countryList.appendChild(row);
        });
      }
    }

    const asnList = document.getElementById('analytics-top-asns');
    if (asnList) {
      asnList.innerHTML = '';
      const asns = geoAsn.top_asns || [];
      if (asns.length === 0) {
        asnList.innerHTML = '<div class="py-3 text-xs text-outline font-mono">No BGP ASN data recorded.</div>';
      } else {
        asns.forEach(a => {
          const row = document.createElement('div');
          row.className = 'flex items-center justify-between py-2 border-b border-surface-container/60 text-xs font-mono';
          row.innerHTML = `
            <div class="flex flex-col truncate max-w-[240px]">
              <span class="text-on-surface font-medium truncate">${escapeHtml(a.org || 'Unknown Org')}</span>
              <span class="text-[10px] text-outline">${escapeHtml(a.asn || 'No ASN')}</span>
            </div>
            <span class="text-secondary font-bold">${a.count} <span class="text-outline font-normal">(${a.pct}%)</span></span>
          `;
          asnList.appendChild(row);
        });
      }
    }

    // ------------------------------------------------------------------------
    // SECTION 6: Research Insights (Deterministic Empirical Findings)
    // ------------------------------------------------------------------------
    const insightsContainer = document.getElementById('analytics-insights-container');
    if (insightsContainer) {
      insightsContainer.innerHTML = '';
      const insights = data.research_insights || [];
      if (insights.length === 0) {
        insightsContainer.innerHTML = '<div class="col-span-full py-3 text-xs text-outline font-mono">Gathering additional observations to establish deterministic patterns.</div>';
      } else {
        const iconMap = {
          security: 'lock',
          infrastructure: 'cloud',
          network: 'router',
          geographic: 'public',
          reputation: 'verified_user'
        };

        insights.forEach(ins => {
          const card = document.createElement('div');
          card.className = 'p-4 rounded-xl glass-panel border border-surface-container flex flex-col justify-between gap-3 shadow-lg';
          const icon = iconMap[ins.category] || 'insights';
          card.innerHTML = `
            <div class="flex items-start justify-between gap-2">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-[18px] text-primary">${icon}</span>
                <h4 class="font-headline text-sm font-semibold text-on-surface">${escapeHtml(ins.title)}</h4>
              </div>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-container text-outline uppercase font-semibold">${escapeHtml(ins.category)}</span>
            </div>
            <p class="text-xs text-on-surface-variant leading-relaxed">${escapeHtml(ins.finding)}</p>
            <div class="pt-2 border-t border-surface-container/60 flex items-center justify-between text-[11px] font-mono">
              <span class="text-outline">Empirical Metric:</span>
              <span class="text-primary font-bold">${escapeHtml(ins.metric)}</span>
            </div>
          `;
          insightsContainer.appendChild(card);
        });
      }
    }

    // ------------------------------------------------------------------------
    // SECTION 7: Comparative Cohort Rankings
    // ------------------------------------------------------------------------
    const cmp = data.comparison_analytics || {};
    const highestTrustTable = document.getElementById('table-highest-trust');
    if (highestTrustTable) {
      highestTrustTable.innerHTML = '';
      const highTrust = cmp.highest_trust_sites || [];
      if (highTrust.length === 0) {
        highestTrustTable.innerHTML = '<tr><td colspan="4" class="py-3 text-center text-outline">No observations recorded.</td></tr>';
      } else {
        highTrust.slice(0, 5).forEach((site, idx) => {
          const tr = document.createElement('tr');
          tr.className = 'hover:bg-surface-container/30 transition-colors';
          tr.innerHTML = `
            <td class="py-2.5 px-2 text-outline font-bold">${idx + 1}</td>
            <td class="py-2.5 px-2 text-on-surface font-semibold truncate max-w-[150px]">${escapeHtml(site.domain)}</td>
            <td class="py-2.5 px-2 text-on-surface-variant">${escapeHtml(site.country || 'Unknown')}</td>
            <td class="py-2.5 px-2 text-right text-emerald-400 font-bold">${site.trust_score !== null ? site.trust_score : '—'}</td>
          `;
          highestTrustTable.appendChild(tr);
        });
      }
    }

    const highestRiskTable = document.getElementById('table-highest-risk');
    if (highestRiskTable) {
      highestRiskTable.innerHTML = '';
      const highRisk = cmp.highest_risk_sites || [];
      if (highRisk.length === 0) {
        highestRiskTable.innerHTML = '<tr><td colspan="4" class="py-3 text-center text-outline">No observations recorded.</td></tr>';
      } else {
        highRisk.slice(0, 5).forEach((site, idx) => {
          const tr = document.createElement('tr');
          tr.className = 'hover:bg-surface-container/30 transition-colors';
          tr.innerHTML = `
            <td class="py-2.5 px-2 text-outline font-bold">${idx + 1}</td>
            <td class="py-2.5 px-2 text-on-surface font-semibold truncate max-w-[150px]">${escapeHtml(site.domain)}</td>
            <td class="py-2.5 px-2 text-on-surface-variant">${escapeHtml(site.infrastructure || 'Unknown')}</td>
            <td class="py-2.5 px-2 text-right text-secondary font-bold">${site.risk_score !== null ? site.risk_score : '—'}</td>
          `;
          highestRiskTable.appendChild(tr);
        });
      }
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

// ----------------------------------------------------------------------------
// Explainable Scoring Modal ("Why this score?")
// ----------------------------------------------------------------------------

let activeScoreModalTab = 'trust';

function openScoreExplanationModal(initialTab = 'trust') {
  activeScoreModalTab = initialTab;
  const modal = document.getElementById('score-explanation-modal');
  if (modal) {
    modal.classList.remove('hidden');
    switchScoreModalTab(activeScoreModalTab);
  }
}

function closeScoreExplanationModal() {
  const modal = document.getElementById('score-explanation-modal');
  if (modal) modal.classList.add('hidden');
}

function switchScoreModalTab(tabName) {
  activeScoreModalTab = tabName;
  const trustBtn = document.getElementById('modal-tab-trust');
  const riskBtn = document.getElementById('modal-tab-risk');

  if (tabName === 'trust') {
    if (trustBtn) {
      trustBtn.className = 'px-4 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer bg-primary/20 text-primary border border-primary/40';
    }
    if (riskBtn) {
      riskBtn.className = 'px-4 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer text-outline hover:text-on-surface hover:bg-surface-container';
    }
  } else {
    if (riskBtn) {
      riskBtn.className = 'px-4 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer bg-secondary/20 text-secondary border border-secondary/40';
    }
    if (trustBtn) {
      trustBtn.className = 'px-4 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer text-outline hover:text-on-surface hover:bg-surface-container';
    }
  }

  renderScoreModalContent();
}

function renderScoreModalContent() {
  const bodyEl = document.getElementById('score-modal-body');
  const disclaimerEl = document.getElementById('score-modal-disclaimer');
  if (!bodyEl) return;

  const data = window.currentAnalysisResult || {};
  const risk = data.risk || {};
  const target = data.target || (data.base && data.base.input) || 'Current Target';

  if (activeScoreModalTab === 'trust') {
    const trust = risk.trust || {};
    const score = typeof trust.score === 'number' ? trust.score : (typeof risk.trust_score === 'number' ? risk.trust_score : 50);
    const classification = trust.classification || (score >= 80 ? 'LIKELY SAFE' : (score >= 60 ? 'GENERALLY SAFE' : (score >= 40 ? 'REVIEW RECOMMENDED' : (score >= 20 ? 'SUSPICIOUS' : 'HIGH RISK'))));
    const confidence = trust.confidence || risk.confidence_rating || 'HIGH';
    const coverage = trust.evidence_coverage || '7/8';
    const signals = trust.signals || [];
    const unknownSignals = trust.unknown_signals || [];

    if (disclaimerEl) {
      disclaimerEl.textContent = trust.disclaimer || 'Website Trust Scores are heuristic analytical assessments derived from observed technical indicators.';
    }

    let signalsHtml = '';
    if (signals.length === 0) {
      signalsHtml = `<div class="p-3 rounded-lg bg-surface-container text-xs text-outline font-mono">No individual signal breakdown records available.</div>`;
    } else {
      signalsHtml = signals.map(s => {
        const isPos = s.points > 0;
        const isNeg = s.points < 0;
        const badgeColor = isPos 
          ? 'bg-tertiary/15 text-tertiary border-tertiary/40' 
          : (isNeg ? 'bg-error/15 text-error border-error/40' : 'bg-surface-container text-outline border-surface-container');
        const pointStr = isPos ? `+${s.points}` : (isNeg ? `${s.points}` : `0`);

        return `
          <div class="p-3 rounded-xl bg-surface-container/70 border border-surface-container flex flex-col gap-1.5 transition-colors hover:bg-surface-container">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-on-surface">${escapeHtml(s.name)}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-mono border ${badgeColor}">${escapeHtml(s.status)}</span>
              </div>
              <span class="px-2 py-0.5 rounded text-xs font-mono font-bold ${isPos ? 'text-tertiary' : (isNeg ? 'text-error' : 'text-outline')}">${pointStr} pts</span>
            </div>
            <p class="text-[12px] text-on-surface-variant leading-normal">${escapeHtml(s.reason)}</p>
            <span class="text-[10px] font-mono text-outline">Source: ${escapeHtml(s.source || 'Security Probe')}</span>
          </div>
        `;
      }).join('');
    }

    let unknownHtml = '';
    if (unknownSignals.length > 0) {
      unknownHtml = `
        <div class="mt-2 flex flex-col gap-2">
          <span class="text-xs font-mono text-outline uppercase tracking-wider font-semibold">Unverified / Neutral Signals (0 pts)</span>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            ${unknownSignals.map(u => `
              <div class="p-2.5 rounded-lg bg-surface-container-lowest/60 border border-surface-container flex flex-col gap-0.5">
                <div class="flex items-center justify-between">
                  <span class="text-[11px] font-mono font-medium text-on-surface">${escapeHtml(u.name)}</span>
                  <span class="text-[10px] font-mono text-outline">Unknown (0)</span>
                </div>
                <span class="text-[10px] text-outline">${escapeHtml(u.reason)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    bodyEl.innerHTML = `
      <!-- Score Hero Summary -->
      <div class="p-4 rounded-xl bg-surface-container-lowest border border-surface-container flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="text-xs font-mono text-outline">Target: <span class="text-on-surface font-semibold">${escapeHtml(target)}</span></div>
          <div class="font-headline text-2xl font-bold text-on-surface mt-1 flex items-baseline gap-2">
            <span class="text-primary">${score}</span>
            <span class="text-sm font-mono text-outline">/ 100</span>
            <span class="ml-2 px-2.5 py-0.5 rounded text-xs font-mono font-semibold bg-tertiary/10 text-tertiary border border-tertiary/30">${escapeHtml(classification)}</span>
          </div>
        </div>
        <div class="flex flex-col md:items-end gap-1">
          <div class="text-xs font-mono text-outline">Evidence Coverage: <span class="text-primary font-semibold">${escapeHtml(coverage)}</span></div>
          <div class="text-xs font-mono text-outline">Confidence Tier: <span class="text-tertiary font-semibold">${escapeHtml(confidence)}</span></div>
        </div>
      </div>

      <!-- Positive & Negative Signal List -->
      <div class="flex flex-col gap-2">
        <span class="text-xs font-mono text-outline uppercase tracking-wider font-semibold">Observed Security Signals</span>
        <div class="flex flex-col gap-2 max-h-64 overflow-y-auto pr-1">
          ${signalsHtml}
        </div>
      </div>

      ${unknownHtml}
    `;
  } else {
    // IP Risk Tab
    const ipRisk = risk.ip_risk || {};
    const score = typeof ipRisk.score === 'number' ? ipRisk.score : (typeof risk.risk_score === 'number' ? risk.risk_score : 5);
    const classification = ipRisk.classification || (score <= 19 ? 'LOW RISK' : (score <= 39 ? 'MODERATE' : (score <= 59 ? 'ELEVATED' : (score <= 79 ? 'HIGH RISK' : 'CRITICAL'))));
    const confidence = ipRisk.confidence || risk.confidence_rating || 'HIGH';
    const coverage = ipRisk.evidence_coverage || '5/5';
    const signals = (ipRisk.signals || []).concat(ipRisk.neutral_signals || []);
    const unknownSignals = ipRisk.unknown_signals || [];

    if (disclaimerEl) {
      disclaimerEl.textContent = ipRisk.disclaimer || 'IP Risk Scores reflect observed network infrastructure indicators and are not definitive proof of maliciousness.';
    }

    let signalsHtml = '';
    if (signals.length === 0) {
      signalsHtml = `<div class="p-3 rounded-lg bg-surface-container text-xs text-outline font-mono">No infrastructure signal records available.</div>`;
    } else {
      signalsHtml = signals.map(s => {
        const isRisk = s.points > 0;
        const isMit = s.points < 0;
        const badgeColor = isRisk 
          ? 'bg-error/15 text-error border-error/40' 
          : (isMit ? 'bg-tertiary/15 text-tertiary border-tertiary/40' : 'bg-surface-container text-outline border-surface-container');
        const pointStr = isRisk ? `+${s.points}` : (isMit ? `${s.points}` : `0`);

        return `
          <div class="p-3 rounded-xl bg-surface-container/70 border border-surface-container flex flex-col gap-1.5 transition-colors hover:bg-surface-container">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-on-surface">${escapeHtml(s.name)}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-mono border ${badgeColor}">${escapeHtml(s.status)}</span>
              </div>
              <span class="px-2 py-0.5 rounded text-xs font-mono font-bold ${isRisk ? 'text-error' : (isMit ? 'text-tertiary' : 'text-outline')}">${pointStr} pts</span>
            </div>
            <p class="text-[12px] text-on-surface-variant leading-normal">${escapeHtml(s.reason)}</p>
            <span class="text-[10px] font-mono text-outline">Source: ${escapeHtml(s.source || 'Infrastructure Classifier')}</span>
          </div>
        `;
      }).join('');
    }

    let unknownHtml = '';
    if (unknownSignals.length > 0) {
      unknownHtml = `
        <div class="mt-2 flex flex-col gap-2">
          <span class="text-xs font-mono text-outline uppercase tracking-wider font-semibold">Unclassified Infrastructure Signals</span>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            ${unknownSignals.map(u => `
              <div class="p-2.5 rounded-lg bg-surface-container-lowest/60 border border-surface-container flex flex-col gap-0.5">
                <div class="flex items-center justify-between">
                  <span class="text-[11px] font-mono font-medium text-on-surface">${escapeHtml(u.name)}</span>
                  <span class="text-[10px] font-mono text-outline">Unknown</span>
                </div>
                <span class="text-[10px] text-outline">${escapeHtml(u.reason)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    bodyEl.innerHTML = `
      <!-- Score Hero Summary -->
      <div class="p-4 rounded-xl bg-surface-container-lowest border border-surface-container flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="text-xs font-mono text-outline">Target: <span class="text-on-surface font-semibold">${escapeHtml(target)}</span></div>
          <div class="font-headline text-2xl font-bold text-on-surface mt-1 flex items-baseline gap-2">
            <span class="text-secondary">${score}</span>
            <span class="text-sm font-mono text-outline">/ 100</span>
            <span class="ml-2 px-2.5 py-0.5 rounded text-xs font-mono font-semibold bg-secondary/10 text-secondary border border-secondary/30">${escapeHtml(classification)}</span>
          </div>
        </div>
        <div class="flex flex-col md:items-end gap-1">
          <div class="text-xs font-mono text-outline">Evidence Coverage: <span class="text-secondary font-semibold">${escapeHtml(coverage)}</span></div>
          <div class="text-xs font-mono text-outline">Confidence Tier: <span class="text-tertiary font-semibold">${escapeHtml(confidence)}</span></div>
        </div>
      </div>

      <!-- Infrastructure Signals List -->
      <div class="flex flex-col gap-2">
        <span class="text-xs font-mono text-outline uppercase tracking-wider font-semibold">Observed Infrastructure Indicators</span>
        <div class="flex flex-col gap-2 max-h-64 overflow-y-auto pr-1">
          ${signalsHtml}
        </div>
      </div>

      ${unknownHtml}
    `;
  }
}

window.openScoreExplanationModal = openScoreExplanationModal;
window.closeScoreExplanationModal = closeScoreExplanationModal;
window.switchScoreModalTab = switchScoreModalTab;

// ----------------------------------------------------------------------------
// Phase 21: Research Report & Data Export UX
// ----------------------------------------------------------------------------

function showExportToast(message, isError = false) {
  let toastEl = document.getElementById('export-toast');
  if (!toastEl) {
    toastEl = document.createElement('div');
    toastEl.id = 'export-toast';
    toastEl.className = 'fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl glass-panel shadow-2xl flex items-center gap-2.5 text-xs font-mono transition-all duration-300 transform translate-y-4 opacity-0 pointer-events-none border';
    document.body.appendChild(toastEl);
  }

  toastEl.className = `fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl glass-panel shadow-2xl flex items-center gap-2.5 text-xs font-mono transition-all duration-300 transform border ${
    isError
      ? 'border-red-500/60 bg-red-950/80 text-red-200'
      : 'border-primary/50 bg-surface-container-high/90 text-on-surface shadow-[0_0_20px_rgba(0,210,255,0.2)]'
  }`;

  const icon = isError ? 'error' : 'check_circle';
  const iconColor = isError ? 'text-red-400' : 'text-primary';
  toastEl.innerHTML = `
    <span class="material-symbols-outlined text-[18px] ${iconColor}">${icon}</span>
    <span>${escapeHtml(message)}</span>
  `;

  requestAnimationFrame(() => {
    toastEl.classList.remove('translate-y-4', 'opacity-0', 'pointer-events-none');
    toastEl.classList.add('translate-y-0', 'opacity-100');
  });

  if (toastEl._hideTimer) clearTimeout(toastEl._hideTimer);
  toastEl._hideTimer = setTimeout(() => {
    toastEl.classList.remove('translate-y-0', 'opacity-100');
    toastEl.classList.add('translate-y-4', 'opacity-0', 'pointer-events-none');
  }, 4500);
}

async function triggerResearchExport(format, btnEl) {
  if (btnEl && btnEl.dataset.loading === 'true') {
    return;
  }

  let originalHtml = '';
  if (btnEl) {
    originalHtml = btnEl.innerHTML;
    btnEl.dataset.loading = 'true';
    btnEl.innerHTML = `
      <span class="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
      <span>Exporting...</span>
    `;
    btnEl.classList.add('opacity-75', 'cursor-wait');
  }

  let endpoint = `${API_BASE}/api/export/csv?type=field-study`;
  let fallbackName = 'IP_PULSE_Field_Study.csv';

  if (format === 'json') {
    endpoint = `${API_BASE}/api/export/json`;
    fallbackName = 'IP_PULSE_Field_Study.json';
  } else if (format === 'report' || format === 'markdown') {
    endpoint = `${API_BASE}/api/export/report`;
    fallbackName = 'IP_PULSE_Research_Report.md';
  } else if (format === 'pdf') {
    endpoint = `${API_BASE}/api/export/pdf`;
    fallbackName = 'IP_PULSE_Research_Report.pdf';
  }

  try {
    const res = await fetch(endpoint);
    if (!res.ok) {
      throw new Error(`Export failed with HTTP status ${res.status}`);
    }

    const disposition = res.headers.get('Content-Disposition') || '';
    let downloadFilename = fallbackName;
    const match = disposition.match(/filename=["']?([^"';]+)["']?/i);
    if (match && match[1]) {
      downloadFilename = match[1];
    }

    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const tempLink = document.createElement('a');
    tempLink.href = blobUrl;
    tempLink.download = downloadFilename;
    document.body.appendChild(tempLink);
    tempLink.click();
    document.body.removeChild(tempLink);
    window.URL.revokeObjectURL(blobUrl);

    try {
      const statusRes = await fetch(`${API_BASE}/api/field-study`);
      if (statusRes.ok) {
        const sData = await statusRes.json();
        const total = sData.total_tested || sData.unique_count || 0;
        const target = sData.target_count || 50;
        if (total >= target) {
          showExportToast(`Field Study target reached: ${total}/${target} observations exported.`);
        } else {
          showExportToast(`Exported ${total} observations. Field Study currently contains ${total}/${target} observations.`);
        }
      } else {
        showExportToast(`Downloaded ${downloadFilename} successfully.`);
      }
    } catch {
      showExportToast(`Downloaded ${downloadFilename} successfully.`);
    }

  } catch (err) {
    console.error('Export error:', err);
    showExportToast(`Export failed: ${err.message}`, true);
  } finally {
    if (btnEl) {
      btnEl.innerHTML = originalHtml;
      btnEl.dataset.loading = 'false';
      btnEl.classList.remove('opacity-75', 'cursor-wait');
    }
  }
}

window.triggerResearchExport = triggerResearchExport;
window.showExportToast = showExportToast;
