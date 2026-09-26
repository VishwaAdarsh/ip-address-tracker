/**
 * IP PULSE - Core Application State & REST API Client
 * Manages view routing, asynchronous lookup requests, real-time polling, and UI rendering.
 */

import { escapeHtml } from './utils.js';
import { initMap, updateMapLocation, resizeMap } from './map.js';

// Centralized API configuration: Reads VITE_API_BASE_URL (configured on Vercel), falls back to window override or same-origin
const API_BASE = (
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
  (typeof window !== 'undefined' && window.__API_BASE_URL__) ||
  ''
).replace(/\/+$/, '');

let currentTarget = null;
let fieldStudyPollingInterval = null;

// Initialize application with readyState fallback
function initApp() {
  initNavigation();
  initHomeTabs();
  initSearch();
  initMap('map', 37.4225, -122.0850);

  // Check initial system status
  fetchSystemStatus();

  // Run initial lookup for google.com if requested
  performAnalysis('google.com');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

// ----------------------------------------------------------------------------
// Mobile Responsive Off-Canvas Navigation
// ----------------------------------------------------------------------------

function openMobileSidebar() {
  const sidebar = document.querySelector('aside');
  const backdrop = document.getElementById('mobile-backdrop');
  if (sidebar) {
    sidebar.classList.remove('-translate-x-full');
    sidebar.classList.add('translate-x-0', 'sidebar-open');
  }
  if (backdrop) {
    backdrop.classList.remove('hidden');
    void backdrop.offsetWidth;
    backdrop.classList.remove('opacity-0');
    backdrop.classList.add('opacity-100');
  }
  document.body.classList.add('mobile-nav-active');
}

function closeMobileSidebar() {
  const sidebar = document.querySelector('aside');
  const backdrop = document.getElementById('mobile-backdrop');
  if (sidebar) {
    sidebar.classList.add('-translate-x-full');
    sidebar.classList.remove('translate-x-0', 'sidebar-open');
  }
  if (backdrop) {
    backdrop.classList.remove('opacity-100');
    backdrop.classList.add('opacity-0');
    setTimeout(() => {
      backdrop.classList.add('hidden');
    }, 280);
  }
  document.body.classList.remove('mobile-nav-active');
}

window.openMobileSidebar = openMobileSidebar;
window.closeMobileSidebar = closeMobileSidebar;

// Global resize and keyboard dismiss listeners
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeMobileSidebar();
    if (typeof closeScoreExplanationModal === 'function') closeScoreExplanationModal();
    if (typeof closeAutoCompleteModal === 'function') closeAutoCompleteModal();
    if (typeof closeFieldStudyDetail === 'function') closeFieldStudyDetail();
    if (typeof closeCandidateModal === 'function') closeCandidateModal();
  }
});

window.addEventListener('resize', () => {
  if (window.innerWidth >= 1024) {
    closeMobileSidebar();
  }
  if (typeof resizeMap === 'function') {
    resizeMap();
  }
  if (window.analyticsMapInstance) {
    window.analyticsMapInstance.invalidateSize();
  }
  if (window.comparisonMapInstance) {
    window.comparisonMapInstance.invalidateSize();
  }
});

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
  if (viewName === 'research-dashboard') {
    viewName = 'analytics';
  }
  const views = ['home', 'history', 'field-study', 'analytics', 'investigation'];
  
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

  // Close mobile drawer upon selection
  closeMobileSidebar();

  // Action on tab switch
  if (viewName === 'home') {
    resizeMap();
  } else if (viewName === 'history') {
    loadHistory();
  } else if (viewName === 'field-study') {
    loadFieldStudy();
  } else if (viewName === 'analytics') {
    loadAnalytics();
    setTimeout(() => {
      if (window.analyticsMapInstance) {
        window.analyticsMapInstance.invalidateSize();
      }
    }, 200);
  } else if (viewName === 'investigation') {
    loadInvestigationWorkspace();
  }
}

// ----------------------------------------------------------------------------
// Search & Analysis Execution
// ----------------------------------------------------------------------------

function initSearch() {
  const input = document.getElementById('ip-search-input');
  const nameInput = document.getElementById('user-name-input');
  const btn = document.getElementById('analyze-btn');

  // Restore stored analyst/user name from localStorage
  if (nameInput) {
    const savedName = localStorage.getItem('ippulse_user_name');
    if (savedName) {
      nameInput.value = savedName;
    }
    nameInput.addEventListener('input', () => {
      localStorage.setItem('ippulse_user_name', (nameInput.value || '').trim());
    });
    nameInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = input ? (input.value || '').trim() : '';
        if (q) performAnalysis(q);
      }
    });
  }

  if (btn && input) {
    btn.addEventListener('click', () => {
      const q = (input.value || '').trim();
      if (q) performAnalysis(q);
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = (input.value || '').trim();
        if (q) performAnalysis(q);
      }
    });
  }
}

// Quick inquiry chips - accessible immediately
function setQuery(q) {
  const input = document.getElementById('ip-search-input');
  if (input) {
    input.value = q;
  }
  performAnalysis(q);
}
window.setQuery = setQuery;

async function performAnalysis(query) {
  if (!query) return;

  const loadingEl = document.getElementById('analysis-loading');
  const errorEl = document.getElementById('analysis-error');
  const loadingMsg = document.getElementById('loading-message');
  const inputEl = document.getElementById('ip-search-input');
  const nameInputEl = document.getElementById('user-name-input');

  if (inputEl) inputEl.value = query;
  currentTarget = query;

  const searchedBy = (nameInputEl && nameInputEl.value ? nameInputEl.value.trim() : '') || localStorage.getItem('ippulse_user_name') || 'Anonymous';

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
      body: JSON.stringify({ target: query, searched_by: searchedBy }),
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

  // Phase 22: Reset AI Explanation view for new scan target
  if (typeof resetAIExplanationView === 'function') {
    resetAIExplanationView();
  }

  // 9. Phase 19: Set current target for Field Study curation
  const currentTarget = data.target || b.input || b.domain || b.selected_ip || '';
  window.currentAnalysisTarget = currentTarget;
  const targetBadge = document.getElementById('active-target-badge');
  if (targetBadge) {
    targetBadge.textContent = currentTarget || 'Current Target';
  }
  const addBtn = document.getElementById('btn-add-to-field-study');
  if (addBtn) {
    if (data.field_study_recorded) {
      addBtn.disabled = true;
      addBtn.innerHTML = `
        <span class="material-symbols-outlined text-[16px] text-emerald-400">check_circle</span>
        <span class="text-emerald-400 font-semibold">Recorded in Field Study</span>
      `;
      addBtn.className = 'px-3 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-xs font-mono text-emerald-400 flex items-center gap-1.5 transition-all cursor-default';
    } else {
      addBtn.disabled = false;
      addBtn.innerHTML = `
        <span class="material-symbols-outlined text-[16px]">biotech</span>
        <span>Add to Field Study</span>
      `;
      addBtn.className = 'px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high border border-surface-container text-xs font-mono text-on-surface flex items-center gap-1.5 transition-all cursor-pointer shadow-sm hover:border-primary/40';
    }
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

function switchHomeTab(tabName) {
  const tabs = ['network', 'security', 'ipintel', 'aireport'];
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
}
window.switchHomeTab = switchHomeTab;

function initHomeTabs() {
  switchHomeTab('network');
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

  const nameInputEl = document.getElementById('user-name-input');
  const searchedBy = (nameInputEl && nameInputEl.value ? nameInputEl.value.trim() : '') || localStorage.getItem('ippulse_user_name') || 'Anonymous';

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
      body: JSON.stringify({ target: target, searched_by: searchedBy })
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
    tableBody.innerHTML = `<tr><td colspan="10" class="py-12 text-center text-outline font-mono">No field study observations recorded yet. Search domains or IP addresses on Home to automatically record and attribute observations.</td></tr>`;
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
      <td class="py-3 px-4 font-mono text-xs text-primary/90 whitespace-nowrap">
        <div class="flex items-center gap-1.5">
          <span class="material-symbols-outlined text-[15px] text-secondary">person</span>
          <span class="truncate max-w-[120px] font-medium">${escapeHtml(r.searched_by || 'Anonymous')}</span>
        </div>
      </td>
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
        <div class="flex justify-between py-1 border-b border-surface-container/50">
          <span class="text-outline">Searched By:</span>
          <span class="text-primary font-semibold truncate flex items-center gap-1">
            <span class="material-symbols-outlined text-[14px] text-secondary">person</span>
            <span>${escapeHtml(obs.searched_by || 'Anonymous')}</span>
          </span>
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
// Analytics View Management (Phase 24 Visualization & Research Dashboard)
// ----------------------------------------------------------------------------

let activeAnalyticsFilters = {
  country: 'all',
  infrastructure: 'all',
  trust_class: 'all',
  risk_class: 'all',
  https_status: 'all',
  ip_version: 'all',
  range: 'all'
};

window.analyticsMapInstance = null;
window.analyticsMarkersLayer = null;

function handleAnalyticsFilterChange(filterKey, filterVal) {
  activeAnalyticsFilters[filterKey] = filterVal;
  loadAnalytics();
}

function resetAnalyticsFilters() {
  activeAnalyticsFilters = {
    country: 'all',
    infrastructure: 'all',
    trust_class: 'all',
    risk_class: 'all',
    https_status: 'all',
    ip_version: 'all',
    range: 'all'
  };

  const selectIds = [
    'dash-filter-country',
    'dash-filter-infra',
    'dash-filter-trust-class',
    'dash-filter-risk-class',
    'dash-filter-https',
    'dash-filter-ip-ver',
    'dash-filter-range'
  ];
  selectIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = 'all';
  });

  loadAnalytics();
}

window.handleAnalyticsFilterChange = handleAnalyticsFilterChange;
window.resetAnalyticsFilters = resetAnalyticsFilters;

function populateAnalyticsFilterDropdowns(options) {
  if (!options) return;

  function updateSelect(id, items, currentVal) {
    const el = document.getElementById(id);
    if (!el || !items) return;
    const selected = currentVal || el.value || 'all';

    const existingValues = Array.from(el.options).map(o => o.value);
    const expectedValues = ['all', ...items];
    const isSame = existingValues.length === expectedValues.length && existingValues.every((v, i) => v === expectedValues[i]);
    if (isSame) {
      el.value = selected;
      return;
    }

    const firstLabel = el.options.length > 0 ? el.options[0].text : 'All';
    el.innerHTML = `<option value="all">${escapeHtml(firstLabel)}</option>`;

    items.forEach(item => {
      const opt = document.createElement('option');
      opt.value = item;
      opt.textContent = item;
      if (item === selected) opt.selected = true;
      el.appendChild(opt);
    });

    el.value = selected;
  }

  if (options.countries) {
    updateSelect('dash-filter-country', options.countries, activeAnalyticsFilters.country);
  }
  if (options.infrastructures) {
    updateSelect('dash-filter-infra', options.infrastructures, activeAnalyticsFilters.infrastructure);
  }
  if (options.trust_classes) {
    updateSelect('dash-filter-trust-class', options.trust_classes, activeAnalyticsFilters.trust_class);
  }
  if (options.risk_classes) {
    updateSelect('dash-filter-risk-class', options.risk_classes, activeAnalyticsFilters.risk_class);
  }
}

function renderAnalyticsMap(mapPoints, missingCount = 0) {
  const mapContainer = document.getElementById('analytics-map');
  if (!mapContainer) return;

  const mapStats = document.getElementById('analytics-map-stats');
  const points = mapPoints || [];
  if (mapStats) {
    mapStats.textContent = `Mapped: ${points.length} endpoints | Missing Coords: ${missingCount}`;
  }

  if (!window.analyticsMapInstance) {
    window.analyticsMapInstance = L.map('analytics-map', {
      zoomControl: true,
      attributionControl: true,
    }).setView([20.0, 0.0], 2);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      subdomains: ['a', 'b', 'c'],
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
    }).addTo(window.analyticsMapInstance);

    window.analyticsMarkersLayer = L.featureGroup().addTo(window.analyticsMapInstance);
  }

  if (window.analyticsMarkersLayer) {
    window.analyticsMarkersLayer.clearLayers();
  }

  if (points.length === 0) {
    window.analyticsMapInstance.setView([20.0, 0.0], 2);
    setTimeout(() => {
      if (window.analyticsMapInstance) window.analyticsMapInstance.invalidateSize();
    }, 100);
    return;
  }

  points.forEach(pt => {
    const customIcon = L.divIcon({
      className: 'analytics-map-marker',
      html: `
        <div style="background: rgba(0, 210, 255, 0.9); width: 12px; height: 12px; border-radius: 50%; border: 2px solid #ffffff; box-shadow: 0 0 10px #00d2ff; cursor: pointer;"></div>
      `,
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    });

    const marker = L.marker([pt.latitude, pt.longitude], { icon: customIcon });
    marker.bindPopup(`
      <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #dfe2ee; background: #0f131c; padding: 8px; border-radius: 6px; min-width: 170px;">
        <div style="color: #a5e7ff; font-weight: bold; font-size: 12px; margin-bottom: 3px;">${escapeHtml(pt.domain || 'Unknown')}</div>
        <div style="color: #949aa7; font-size: 10px; margin-bottom: 4px;">${escapeHtml([pt.city, pt.country].filter(Boolean).join(', ') || 'Unknown Location')}</div>
        <div style="margin-bottom: 2px;"><span style="color: #64748b;">IP:</span> <span style="color: #ffffff;">${escapeHtml(pt.resolved_ip || '—')}</span></div>
        <div style="margin-bottom: 2px;"><span style="color: #64748b;">Infra:</span> <span style="color: #e2e8f0;">${escapeHtml(pt.infrastructure || '—')}</span></div>
        <div style="margin-top: 4px; padding-top: 4px; border-top: 1px solid #1e293b; display: flex; justify-content: space-between;">
          <span style="color: #69f6b9; font-weight: 600;">Trust: ${pt.trust_score !== null && pt.trust_score !== undefined ? pt.trust_score : '—'}</span>
          <span style="color: #ffb4ab; font-weight: 600;">Risk: ${pt.risk_score !== null && pt.risk_score !== undefined ? pt.risk_score : '—'}</span>
        </div>
      </div>
    `);
    window.analyticsMarkersLayer.addLayer(marker);
  });

  try {
    const bounds = window.analyticsMarkersLayer.getBounds();
    if (bounds.isValid()) {
      window.analyticsMapInstance.fitBounds(bounds.pad(0.2));
    }
  } catch (err) {
    console.debug('Analytics map fitBounds error:', err);
  }

  setTimeout(() => {
    if (window.analyticsMapInstance) window.analyticsMapInstance.invalidateSize();
  }, 150);
}

async function loadAnalytics() {
  const container = document.getElementById('analytics-content');
  const emptyBanner = document.getElementById('analytics-empty');
  const filterEmptyBanner = document.getElementById('analytics-filter-empty');
  const loadingSkeleton = document.getElementById('analytics-loading');

  // Build query string from active filters
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(activeAnalyticsFilters)) {
    if (v && v !== 'all') {
      params.set(k, v);
    }
  }
  const queryString = params.toString();
  const url = queryString ? `${API_BASE}/api/analytics?${queryString}` : `${API_BASE}/api/analytics`;

  try {
    if (loadingSkeleton && (!container || container.classList.contains('hidden'))) {
      loadingSkeleton.classList.remove('hidden');
    }

    const res = await fetch(url);
    const data = await res.json();

    if (loadingSkeleton) loadingSkeleton.classList.add('hidden');

    if (!res.ok || !data.success) {
      if (container) container.classList.add('hidden');
      if (emptyBanner) emptyBanner.classList.remove('hidden');
      if (filterEmptyBanner) filterEmptyBanner.classList.add('hidden');
      return;
    }

    // Populate filter dropdowns dynamically from real values
    if (data.available_filter_options) {
      populateAnalyticsFilterDropdowns(data.available_filter_options);
    }

    const totalObs = data.unfiltered_total_count !== undefined ? data.unfiltered_total_count : (data.overview ? data.overview.total_observations : 0);
    const validObs = data.valid_observations !== undefined ? data.valid_observations : (data.overview && data.overview.valid_observations !== undefined ? data.overview.valid_observations : totalObs);
    const failedObs = data.failed_observations !== undefined ? data.failed_observations : (data.overview && data.overview.failed_observations !== undefined ? data.overview.failed_observations : 0);
    const sampleTarget = (data.overview && data.overview.sample_target) || 50;
    const pctComplete = sampleTarget > 0 ? Math.round((totalObs / sampleTarget) * 100) : 0;
    const remaining = Math.max(0, sampleTarget - totalObs);
    const targetReached = totalObs >= sampleTarget;

    // Update Progress Card Header (always reflect real dataset count)
    setText('dash-prog-count-display', `${totalObs} / ${sampleTarget}`);
    setText('dash-prog-pct-label', `(${pctComplete}% Complete)`);
    setText('dash-prog-remaining-display', targetReached ? 'Sample quota target fulfilled (50/50)' : `${remaining} observations remaining`);
    setText('dash-prog-valid-pill', `Valid: ${validObs}`);
    setText('dash-prog-failed-pill', `Failed: ${failedObs}`);

    const quotaBadge = document.getElementById('dash-prog-quota-badge');
    if (quotaBadge) {
      if (targetReached) {
        quotaBadge.textContent = 'Quota Fulfilled (50/50)';
        quotaBadge.className = 'px-3 py-1 rounded-lg text-xs font-mono font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30';
      } else {
        quotaBadge.textContent = `${pctComplete}% Complete`;
        quotaBadge.className = 'px-3 py-1 rounded-lg text-xs font-mono font-semibold bg-primary/15 text-primary border border-primary/30';
      }
    }

    const dashProgBar = document.getElementById('dash-prog-bar');
    if (dashProgBar) {
      dashProgBar.style.width = `${Math.min(pctComplete, 100)}%`;
    }

    // Top status badges
    const analyticsNCount = document.getElementById('analytics-n-count');
    if (analyticsNCount) {
      if (data.is_filtered) {
        analyticsNCount.textContent = `N = ${data.filtered_count} Filtered (${totalObs} Total) / ${sampleTarget} Observed Endpoints`;
      } else {
        analyticsNCount.textContent = `N = ${totalObs} / ${sampleTarget} Observed Endpoints`;
      }
    }
    const statusBadge = document.getElementById('analytics-status-badge');
    if (statusBadge) {
      if (targetReached) {
        statusBadge.textContent = 'TARGET ACHIEVED';
        statusBadge.className = 'ml-2 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30';
      } else {
        statusBadge.textContent = 'INCOMPLETE';
        statusBadge.className = 'ml-2 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-primary/10 text-primary border border-primary/30';
      }
    }

    // Filter indicator banner
    const filterIndicator = document.getElementById('dash-filter-indicator');
    const filterIndicatorText = document.getElementById('dash-filter-indicator-text');
    if (data.is_filtered) {
      if (filterIndicator) filterIndicator.classList.remove('hidden');
      if (filterIndicatorText) {
        filterIndicatorText.textContent = `Filtered Cohort Active: Showing ${data.filtered_count} of ${totalObs} observations (${data.filter_summary || 'Custom Filter'})`;
      }
    } else {
      if (filterIndicator) filterIndicator.classList.add('hidden');
    }

    // Handle Empty Database State (zero observations total)
    if (totalObs === 0) {
      if (container) container.classList.add('hidden');
      if (emptyBanner) emptyBanner.classList.remove('hidden');
      if (filterEmptyBanner) filterEmptyBanner.classList.add('hidden');
      return;
    }

    // Handle Filter Empty State (records exist in DB, but 0 match active filter)
    const cohortCount = data.is_filtered ? data.filtered_count : (data.overview ? data.overview.total_observations : 0);
    if (data.is_filtered && cohortCount === 0) {
      if (container) container.classList.add('hidden');
      if (emptyBanner) emptyBanner.classList.add('hidden');
      if (filterEmptyBanner) filterEmptyBanner.classList.remove('hidden');
      return;
    }

    // Normal State with Data
    if (container) container.classList.remove('hidden');
    if (emptyBanner) emptyBanner.classList.add('hidden');
    if (filterEmptyBanner) filterEmptyBanner.classList.add('hidden');

    const ov = data.overview || {};
    const total = cohortCount;

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
    setText('analytics-progress-pct-label', `${ov.collection_progress_pct}% Quota Fulfilled`);

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
      if (bar) {
        bar.style.height = `${Math.max(b.pct, 4)}%`;
        bar.title = `${b.bin_label || b.range}: ${b.count} endpoints (${b.pct}%)`;
        if (bar.parentElement) {
          bar.parentElement.title = `${b.bin_label || b.range}: ${b.count} endpoints (${b.pct}%)`;
        }
      }
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
      if (bar) {
        bar.style.height = `${Math.max(b.pct, 4)}%`;
        bar.title = `${b.bin_label || b.range}: ${b.count} endpoints (${b.pct}%)`;
        if (bar.parentElement) {
          bar.parentElement.title = `${b.bin_label || b.range}: ${b.count} endpoints (${b.pct}%)`;
        }
      }
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
    // SECTION 5: Country & Interactive Geographic Map
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

    // Render interactive Leaflet map
    renderAnalyticsMap(data.map_points || [], data.missing_coordinates_count || 0);

    // ------------------------------------------------------------------------
    // SECTION 6: Autonomous Systems & Research Findings
    // ------------------------------------------------------------------------
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
    if (loadingSkeleton) loadingSkeleton.classList.add('hidden');
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

// =============================================================================
// PHASE 22: EXPLAINABLE AI INTELLIGENCE LAYER
// =============================================================================

let _isExplainingAI = false;

function resetAIExplanationView() {
  const idleEl = document.getElementById('ai-explanation-idle');
  const loadingEl = document.getElementById('ai-explanation-loading');
  const errorEl = document.getElementById('ai-explanation-error');
  const resultEl = document.getElementById('ai-explanation-result');
  const btnEl = document.getElementById('btn-generate-ai-explanation');
  const iconEl = document.getElementById('ai-btn-icon');
  const labelEl = document.getElementById('ai-btn-label');

  if (idleEl) idleEl.classList.remove('hidden');
  if (loadingEl) loadingEl.classList.add('hidden');
  if (errorEl) errorEl.classList.add('hidden');
  if (resultEl) resultEl.classList.add('hidden');

  if (btnEl) {
    btnEl.disabled = false;
    btnEl.classList.remove('opacity-50', 'cursor-not-allowed');
  }
  if (iconEl) iconEl.textContent = 'auto_awesome';
  if (labelEl) labelEl.textContent = 'Explain with AI';

  _isExplainingAI = false;
}

async function fetchAIProviderStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/explain/status`);
    if (res.ok) {
      const data = await res.json();
      const badge = document.getElementById('ai-provider-badge');
      if (badge) {
        const providerUpper = (data.provider || 'AI').toUpperCase();
        badge.textContent = `ENGINE: ${providerUpper}`;
        badge.title = `Model: ${data.model || 'default'} • Status: ${data.status || 'operational'}`;
      }
    }
  } catch (err) {
    console.debug('AI provider status check failed:', err);
  }
}

function renderSignalList(containerId, signals, dotClass) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';

  if (!signals || signals.length === 0) {
    const emptyEl = document.createElement('div');
    emptyEl.className = 'text-[11px] text-outline italic py-0.5';
    emptyEl.textContent = 'None identified';
    container.appendChild(emptyEl);
    return;
  }

  signals.forEach(sig => {
    const item = document.createElement('div');
    item.className = 'flex items-start gap-1.5 text-[11px] text-on-surface-variant leading-snug';
    item.innerHTML = `
      <span class="mt-1 w-1 h-1 rounded-full ${dotClass} shrink-0"></span>
      <span>${sig}</span>
    `;
    container.appendChild(item);
  });
}

async function triggerAIExplanation() {
  if (_isExplainingAI) return;

  const currentData = window.currentAnalysisResult;
  if (!currentData || !currentData.target) {
    alert('Please analyze a website or IP address first.');
    return;
  }

  const idleEl = document.getElementById('ai-explanation-idle');
  const loadingEl = document.getElementById('ai-explanation-loading');
  const errorEl = document.getElementById('ai-explanation-error');
  const errorMsgEl = document.getElementById('ai-error-message');
  const resultEl = document.getElementById('ai-explanation-result');
  const btnEl = document.getElementById('btn-generate-ai-explanation');
  const iconEl = document.getElementById('ai-btn-icon');
  const labelEl = document.getElementById('ai-btn-label');

  _isExplainingAI = true;

  if (idleEl) idleEl.classList.add('hidden');
  if (errorEl) errorEl.classList.add('hidden');
  if (resultEl) resultEl.classList.add('hidden');
  if (loadingEl) loadingEl.classList.remove('hidden');

  if (btnEl) {
    btnEl.disabled = true;
    btnEl.classList.add('opacity-50', 'cursor-not-allowed');
  }
  if (iconEl) iconEl.textContent = 'progress_activity';
  if (labelEl) labelEl.textContent = 'Analyzing...';

  try {
    const res = await fetch(`${API_BASE}/api/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target: currentData.target,
        intelligence: currentData,
      }),
    });

    const data = await res.json();

    if (!res.ok || data.status === 'error' || data.status === 'provider_unavailable') {
      if (loadingEl) loadingEl.classList.add('hidden');
      if (errorEl) errorEl.classList.remove('hidden');
      if (errorMsgEl) {
        errorMsgEl.textContent = data.summary || data.error || 'AI explanation unavailable. Deterministic analysis remains fully available.';
      }
      return;
    }

    // Success State - Render Explanation Details
    if (loadingEl) loadingEl.classList.add('hidden');
    if (resultEl) resultEl.classList.remove('hidden');

    setText('ai-summary-text', data.summary || 'Summary unavailable.');
    setText('ai-trust-explanation-text', data.trust_explanation || 'Trust explanation unavailable.');
    setText('ai-risk-explanation-text', data.risk_explanation || 'Risk explanation unavailable.');

    renderSignalList('ai-positive-signals-list', data.positive_signals || [], 'bg-tertiary');
    renderSignalList('ai-negative-signals-list', data.negative_signals || [], 'bg-error');
    renderSignalList('ai-unknown-signals-list', data.unknown_signals || [], 'bg-outline');

    setText('ai-recommendation-text', data.recommendation || 'Standard verification precautions apply.');
    setText('ai-limitations-text', data.limitations || 'AI explanations interpret empirical scan telemetry. Deterministic classifications and technical evidence remain authoritative.');

    // Update button to allow re-explaining
    if (labelEl) labelEl.textContent = 'Re-explain';
    if (iconEl) iconEl.textContent = 'refresh';

  } catch (err) {
    console.error('AI Explanation failed:', err);
    if (loadingEl) loadingEl.classList.add('hidden');
    if (errorEl) errorEl.classList.remove('hidden');
    if (errorMsgEl) {
      errorMsgEl.textContent = `AI request failed: ${err.message}. Deterministic analysis is fully operational.`;
    }
  } finally {
    _isExplainingAI = false;
    if (btnEl) {
      btnEl.disabled = false;
      btnEl.classList.remove('opacity-50', 'cursor-not-allowed');
    }
  }
}

// Global exports
window.triggerAIExplanation = triggerAIExplanation;
window.resetAIExplanationView = resetAIExplanationView;
window.fetchAIProviderStatus = fetchAIProviderStatus;

// Initialize AI provider telemetry on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', fetchAIProviderStatus);
} else {
  fetchAIProviderStatus();
}

// =============================================================================
// PHASE 23: INTELLIGENCE COMPARISON & INVESTIGATION WORKSPACE
// =============================================================================

window.selectedComparisonItems = [];
window.availableCandidates = [];
window.currentComparisonResult = null;
window.candidateFilterType = 'all';
window.compMapInstance = null;
window.compMarkersLayer = null;
window._isExplainingComparisonAI = false;

function loadInvestigationWorkspace() {
  updateComparisonSelectionUI();
  if (window.compMapInstance) {
    setTimeout(() => {
      window.compMapInstance.invalidateSize();
    }, 150);
  }
}

function updateComparisonSelectionUI() {
  const countBadge = document.getElementById('comp-selection-count-badge');
  const hintEl = document.getElementById('comp-validation-hint');
  const chipsContainer = document.getElementById('comp-selected-chips-container');
  const runBtn = document.getElementById('btn-run-comparison');
  const modalCount = document.getElementById('comp-modal-selection-count');

  const count = window.selectedComparisonItems.length;

  if (countBadge) {
    countBadge.textContent = `${count} / 5 Selected`;
  }
  if (modalCount) {
    modalCount.textContent = `${count} / 5 Selected`;
  }

  if (chipsContainer) {
    chipsContainer.innerHTML = '';
    if (count === 0) {
      chipsContainer.innerHTML = `
        <div class="text-xs text-outline font-mono italic py-1">
          No observations selected. Add 2 to 5 observations from Field Study, History, or Current Scan.
        </div>
      `;
    } else {
      window.selectedComparisonItems.forEach((item, idx) => {
        const chip = document.createElement('div');
        chip.className = 'inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-container-high border border-surface-container text-xs text-on-surface font-mono shadow-sm';
        
        let sourceClass = 'bg-primary/10 text-primary border-primary/20';
        let sourceLabel = 'Current';
        if (item.source === 'field_study') {
          sourceClass = 'bg-tertiary/10 text-tertiary border-tertiary/20';
          sourceLabel = 'Field Study';
        } else if (item.source === 'history') {
          sourceClass = 'bg-secondary/10 text-secondary border-secondary/20';
          sourceLabel = 'History';
        }

        chip.innerHTML = `
          <span class="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold border ${sourceClass}">${sourceLabel}</span>
          <span class="font-medium">${item.domain || item.resolved_ip || 'Unknown'}</span>
          <button type="button" class="text-outline hover:text-error transition-colors cursor-pointer ml-1" onclick="removeComparisonItem(${idx})" title="Remove">
            <span class="material-symbols-outlined text-[15px]">close</span>
          </button>
        `;
        chipsContainer.appendChild(chip);
      });
    }
  }

  if (hintEl) {
    if (count < 2) {
      hintEl.textContent = `Select at least 2 observations to activate comparison (${2 - count} remaining).`;
      hintEl.classList.remove('text-tertiary');
      hintEl.classList.add('text-outline');
    } else {
      hintEl.textContent = `Ready: ${count} observations selected. Maximum limit is 5.`;
      hintEl.classList.remove('text-outline');
      hintEl.classList.add('text-tertiary');
    }
  }

  if (runBtn) {
    runBtn.disabled = count < 2 || count > 5;
  }
}

function removeComparisonItem(idx) {
  if (idx >= 0 && idx < window.selectedComparisonItems.length) {
    window.selectedComparisonItems.splice(idx, 1);
    updateComparisonSelectionUI();
  }
}

async function openCandidateModal(defaultTab = 'all') {
  window.candidateFilterType = defaultTab;
  const modal = document.getElementById('comp-candidate-modal');
  if (modal) modal.classList.remove('hidden');

  setCandidateFilter(defaultTab);

  const listEl = document.getElementById('comp-candidate-list');
  if (listEl) {
    listEl.innerHTML = `
      <div class="flex items-center justify-center p-8 gap-2 text-outline text-xs font-mono">
        <span class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
        <span>Loading observation records...</span>
      </div>
    `;
  }

  try {
    const res = await fetch(`${API_BASE}/api/compare/candidates`);
    if (res.ok) {
      const data = await res.json();
      window.availableCandidates = data.candidates || [];
      renderCandidateList();
    } else {
      if (listEl) listEl.innerHTML = `<div class="p-4 text-xs text-error font-mono">Failed to load candidates.</div>`;
    }
  } catch (err) {
    if (listEl) listEl.innerHTML = `<div class="p-4 text-xs text-error font-mono">Network error: ${err.message}</div>`;
  }
}

function closeCandidateModal() {
  const modal = document.getElementById('comp-candidate-modal');
  if (modal) modal.classList.add('hidden');
  updateComparisonSelectionUI();
}

function setCandidateFilter(type) {
  window.candidateFilterType = type;
  const tabs = ['all', 'field_study', 'history'];
  tabs.forEach(t => {
    const btn = document.getElementById(`comp-tab-${t.replace('_', '-')}`);
    if (btn) {
      if (t === type) {
        btn.classList.add('bg-surface-container-high', 'text-primary');
        btn.classList.remove('text-outline');
      } else {
        btn.classList.remove('bg-surface-container-high', 'text-primary');
        btn.classList.add('text-outline');
      }
    }
  });
  renderCandidateList();
}

function filterCandidateList() {
  renderCandidateList();
}

function renderCandidateList() {
  const listEl = document.getElementById('comp-candidate-list');
  const searchInput = document.getElementById('comp-candidate-search');
  if (!listEl) return;

  const query = (searchInput ? searchInput.value : '').trim().toLowerCase();
  const filterType = window.candidateFilterType;

  const filtered = (window.availableCandidates || []).filter(c => {
    if (filterType !== 'all' && c.source !== filterType) return false;
    if (!query) return true;
    const text = `${c.domain} ${c.ip_address} ${c.asn} ${c.organization} ${c.country} ${c.city}`.toLowerCase();
    return text.includes(query);
  });

  listEl.innerHTML = '';

  if (filtered.length === 0) {
    listEl.innerHTML = `
      <div class="text-center p-6 text-xs text-outline font-mono">
        No matching observation candidates found.
      </div>
    `;
    return;
  }

  filtered.forEach(c => {
    const isSelected = window.selectedComparisonItems.some(
      it => (it.domain && it.domain.toLowerCase() === (c.domain || '').toLowerCase())
    );

    const row = document.createElement('div');
    row.className = `p-3 rounded-xl border transition-all flex items-center justify-between gap-3 cursor-pointer ${
      isSelected
        ? 'bg-primary/10 border-primary/40'
        : 'bg-surface-container-lowest/80 border-surface-container hover:border-surface-container-high'
    }`;

    row.onclick = () => toggleCandidateSelection(c);

    let scorePill = '';
    if (typeof c.trust_score === 'number' && typeof c.risk_score === 'number') {
      scorePill = `
        <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-tertiary/10 text-tertiary border border-tertiary/20">Trust ${c.trust_score}</span>
        <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-secondary/10 text-secondary border border-secondary/20">Risk ${c.risk_score}</span>
      `;
    }

    row.innerHTML = `
      <div class="flex items-center gap-3 min-w-0">
        <input type="checkbox" class="rounded bg-surface-container border-surface-container text-primary pointer-events-none" ${isSelected ? 'checked' : ''}>
        <div class="flex flex-col min-w-0">
          <div class="flex items-center gap-2">
            <span class="font-mono text-xs font-semibold text-on-surface truncate">${c.domain || 'Unknown Target'}</span>
            <span class="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-surface-container text-outline border border-surface-container">${c.badge || c.source}</span>
          </div>
          <div class="flex items-center gap-2 text-[11px] font-mono text-outline truncate mt-0.5">
            <span>${c.ip_address || 'No IP'}</span>
            <span>•</span>
            <span>${c.asn || 'No ASN'}</span>
            <span>•</span>
            <span>${c.city || 'Unknown'}, ${c.country || ''}</span>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        ${scorePill}
        <span class="text-[11px] font-mono ${isSelected ? 'text-primary font-bold' : 'text-outline'}">
          ${isSelected ? 'Selected' : '+ Add'}
        </span>
      </div>
    `;

    listEl.appendChild(row);
  });
}

function toggleCandidateSelection(candidate) {
  const domKey = (candidate.domain || '').trim().toLowerCase();
  const existingIdx = window.selectedComparisonItems.findIndex(
    it => (it.domain && it.domain.toLowerCase() === domKey)
  );

  if (existingIdx >= 0) {
    window.selectedComparisonItems.splice(existingIdx, 1);
  } else {
    if (window.selectedComparisonItems.length >= 5) {
      alert('A maximum of 5 observations can be selected for comparison.');
      return;
    }
    window.selectedComparisonItems.push({
      id: candidate.id,
      source: candidate.source,
      domain: candidate.domain,
      resolved_ip: candidate.ip_address,
      country: candidate.country,
      city: candidate.city,
      asn: candidate.asn,
      organization: candidate.organization,
      website_trust_score: candidate.trust_score,
      ip_risk_score: candidate.risk_score,
    });
  }

  renderCandidateList();
  updateComparisonSelectionUI();
}

function addCurrentScanToComparison() {
  const current = window.currentAnalysisResult;
  if (!current || !current.target) {
    alert('Please analyze a website or IP address on the Home page first.');
    return;
  }

  const domKey = (current.target || '').trim().toLowerCase();
  const exists = window.selectedComparisonItems.some(
    it => (it.domain && it.domain.toLowerCase() === domKey)
  );

  if (exists) {
    alert(`Target '${current.target}' is already included in comparison candidates.`);
    return;
  }

  if (window.selectedComparisonItems.length >= 5) {
    alert('A maximum of 5 observations can be selected for comparison.');
    return;
  }

  const base = current.base || {};
  const sec = current.security || {};
  const intel = current.ip_intel || {};
  const risk = current.risk || {};

  window.selectedComparisonItems.push({
    source: 'current',
    domain: current.target,
    resolved_ip: base.selected_ip || intel.ip_address || 'UNKNOWN',
    ip_version: base.ip_version || 'IPv4',
    country: base.country || 'Unknown',
    region: base.region || 'Unknown',
    city: base.city || 'Unknown',
    latitude: base.latitude,
    longitude: base.longitude,
    asn: base.asn || intel.asn || 'Unknown',
    organization: base.organization || intel.organization || 'Unknown',
    isp: base.isp || intel.isp || 'Unknown',
    infrastructure_type: intel.infrastructure_type || 'Unknown',
    network_type: intel.network_type || 'Unknown',
    https_status: sec.is_https ? 'Enabled' : 'Disabled',
    tls_status: sec.tls_valid ? 'Valid' : 'Invalid / Expired',
    tls_version: sec.tls_version || 'UNKNOWN',
    tls_issuer: sec.issuer_org || 'UNKNOWN',
    ssl_expiry_days: sec.expires_in_days !== undefined ? String(sec.expires_in_days) : 'UNKNOWN',
    vpn_status: intel.vpn_status || 'NOT_DETECTED',
    proxy_status: intel.proxy_status || 'NOT_DETECTED',
    tor_status: intel.tor_status || 'NOT_DETECTED',
    datacenter_status: intel.datacenter_status || 'NOT_DETECTED',
    website_trust_score: risk.trust_score,
    website_trust_classification: risk.trust?.classification || 'UNKNOWN',
    ip_risk_score: risk.risk_score,
    ip_risk_classification: risk.risk_category || 'UNKNOWN',
    score_confidence: risk.confidence_rating || 'UNKNOWN',
    ip_personality: current.personality || 'Network host endpoint',
  });

  updateComparisonSelectionUI();
  showExportToast(`Added current scan '${current.target}' to comparison selection.`);
}

function clearComparisonSelection() {
  window.selectedComparisonItems = [];
  window.currentComparisonResult = null;
  const bodyEl = document.getElementById('comp-workspace-body');
  if (bodyEl) bodyEl.classList.add('hidden');

  const csvBtn = document.getElementById('btn-export-comp-csv');
  const jsonBtn = document.getElementById('btn-export-comp-json');
  if (csvBtn) csvBtn.disabled = true;
  if (jsonBtn) jsonBtn.disabled = true;

  updateComparisonSelectionUI();
}

async function runInvestigationComparison() {
  if (window.selectedComparisonItems.length < 2) {
    alert('Please select at least 2 observations to run comparison.');
    return;
  }

  const runBtn = document.getElementById('btn-run-comparison');
  const statusText = document.getElementById('comp-status-text');
  const bodyEl = document.getElementById('comp-workspace-body');

  if (runBtn) {
    runBtn.disabled = true;
    runBtn.innerHTML = `
      <span class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
      <span>Comparing...</span>
    `;
  }
  if (statusText) statusText.textContent = 'Normalizing telemetry and computing differences...';

  try {
    const res = await fetch(`${API_BASE}/api/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ observations: window.selectedComparisonItems }),
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Comparison computation failed.');
    }

    window.currentComparisonResult = data;

    if (bodyEl) bodyEl.classList.remove('hidden');

    renderComparisonMatrix(data.observations || []);
    renderComparisonStatistics(data.statistics || {});
    renderDifferenceHighlights(data.differences || []);
    renderComparisonMap(data.map_points || []);

    const csvBtn = document.getElementById('btn-export-comp-csv');
    const jsonBtn = document.getElementById('btn-export-comp-json');
    if (csvBtn) csvBtn.disabled = false;
    if (jsonBtn) jsonBtn.disabled = false;

    // Reset AI state
    resetComparisonAIView();

    if (statusText) statusText.textContent = `Comparison active for ${data.count} observations.`;

  } catch (err) {
    console.error('Comparison error:', err);
    alert(`Comparison failed: ${err.message}`);
    if (statusText) statusText.textContent = 'Comparison failed.';
  } finally {
    if (runBtn) {
      runBtn.disabled = false;
      runBtn.innerHTML = `
        <span class="material-symbols-outlined text-[18px]">balance</span>
        <span>Compare Selected Targets</span>
      `;
    }
  }
}

function renderComparisonMatrix(observations) {
  const thead = document.getElementById('comp-matrix-thead');
  const tbody = document.getElementById('comp-matrix-tbody');
  if (!thead || !tbody) return;

  // Build Table Header
  let headerHtml = `
    <tr>
      <th class="p-3 font-mono text-[11px] text-outline uppercase tracking-wider bg-surface-container-lowest min-w-[180px] border-r border-surface-container">
        Attribute Dimension
      </th>
  `;

  observations.forEach(obs => {
    let sourcePill = '<span class="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-primary/10 text-primary border border-primary/20">Current</span>';
    if (obs.source === 'field_study') {
      sourcePill = '<span class="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-tertiary/10 text-tertiary border border-tertiary/20">Field Study</span>';
    } else if (obs.source === 'history') {
      sourcePill = '<span class="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-secondary/10 text-secondary border border-secondary/20">History</span>';
    }

    headerHtml += `
      <th class="p-3 font-mono text-xs text-on-surface min-w-[220px]">
        <div class="flex items-center justify-between gap-2">
          <span class="font-bold text-primary truncate">${obs.domain}</span>
          ${sourcePill}
        </div>
        <div class="text-[11px] text-outline font-normal mt-0.5">${obs.resolved_ip}</div>
      </th>
    `;
  });
  headerHtml += `</tr>`;
  thead.innerHTML = headerHtml;

  // Rows definition
  const sections = [
    {
      title: 'IDENTITY & RESOLUTION',
      rows: [
        { label: 'Target Domain', prop: 'domain' },
        { label: 'Resolved Primary IP', prop: 'resolved_ip' },
      ],
    },
    {
      title: 'NETWORK INFRASTRUCTURE',
      rows: [
        { label: 'IP Version', prop: 'ip_version' },
        { label: 'Autonomous System (ASN)', prop: 'asn' },
        { label: 'Organization', prop: 'organization' },
        { label: 'ISP / Carrier', prop: 'isp' },
        { label: 'Network Type', prop: 'network_type' },
        { label: 'Infrastructure Type', prop: 'infrastructure_type' },
      ],
    },
    {
      title: 'GEOLOCATION TELEMETRY',
      rows: [
        { label: 'Country', prop: 'country' },
        { label: 'Region / State', prop: 'region' },
        { label: 'City', prop: 'city' },
        { label: 'Coordinates (Lat, Lon)', format: (o) => (o.latitude !== null && o.longitude !== null ? `${o.latitude.toFixed(4)}°, ${o.longitude.toFixed(4)}°` : 'UNKNOWN') },
        { label: 'Geolocation Confidence', prop: 'geolocation_confidence' },
      ],
    },
    {
      title: 'TRANSPORT SECURITY',
      rows: [
        { label: 'HTTPS Status', format: (o) => o.https_status === 'Enabled' ? '<span class="text-tertiary font-medium">Enabled</span>' : (o.https_status === 'Disabled' ? '<span class="text-error font-medium">Disabled</span>' : '<span class="text-outline">UNKNOWN</span>') },
        { label: 'TLS Validation', format: (o) => o.tls_status === 'Valid' ? '<span class="text-tertiary">Valid</span>' : (o.tls_status === 'Invalid / Expired' ? '<span class="text-error">Invalid / Expired</span>' : '<span class="text-outline">UNKNOWN</span>') },
        { label: 'TLS Protocol Version', prop: 'tls_version' },
        { label: 'Certificate Issuer', prop: 'tls_issuer' },
        { label: 'Certificate Validity Days', prop: 'ssl_expiry_days' },
      ],
    },
    {
      title: 'IP INTELLIGENCE & PROVENANCE',
      rows: [
        { label: 'VPN Detection', format: (o) => o.vpn_status === 'DETECTED' ? '<span class="text-error font-medium">DETECTED</span>' : (o.vpn_status === 'NOT_DETECTED' ? '<span class="text-outline">NOT DETECTED</span>' : '<span class="text-outline">UNKNOWN</span>') },
        { label: 'Proxy Detection', format: (o) => o.proxy_status === 'DETECTED' ? '<span class="text-error font-medium">DETECTED</span>' : (o.proxy_status === 'NOT_DETECTED' ? '<span class="text-outline">NOT DETECTED</span>' : '<span class="text-outline">UNKNOWN</span>') },
        { label: 'Tor Exit Relay', format: (o) => o.tor_status === 'DETECTED' ? '<span class="text-error font-medium">DETECTED</span>' : (o.tor_status === 'NOT_DETECTED' ? '<span class="text-outline">NOT DETECTED</span>' : '<span class="text-outline">UNKNOWN</span>') },
        { label: 'Datacenter / Hosting', format: (o) => o.datacenter_status === 'DETECTED' ? '<span class="text-secondary font-medium">DETECTED</span>' : (o.datacenter_status === 'NOT_DETECTED' ? '<span class="text-outline">NOT DETECTED</span>' : '<span class="text-outline">UNKNOWN</span>') },
      ],
    },
    {
      title: 'RISK & TRUST EVALUATION',
      rows: [
        {
          label: 'Website Trust Score',
          format: (o) => o.website_trust_score !== null && o.website_trust_score !== undefined
            ? `<span class="px-2 py-0.5 rounded text-xs font-mono font-bold ${o.website_trust_score >= 70 ? 'bg-tertiary/10 text-tertiary border border-tertiary/30' : (o.website_trust_score >= 40 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' : 'bg-error/10 text-error border border-error/30')}">${o.website_trust_score}/100</span>`
            : '<span class="text-outline">N/A</span>'
        },
        { label: 'Trust Classification', prop: 'website_trust_classification' },
        {
          label: 'IP Risk Score',
          format: (o) => o.ip_risk_score !== null && o.ip_risk_score !== undefined
            ? `<span class="px-2 py-0.5 rounded text-xs font-mono font-bold ${o.ip_risk_score <= 25 ? 'bg-tertiary/10 text-tertiary border border-tertiary/30' : (o.ip_risk_score <= 60 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' : 'bg-error/10 text-error border border-error/30')}">${o.ip_risk_score}/100</span>`
            : '<span class="text-outline">N/A</span>'
        },
        { label: 'IP Risk Classification', prop: 'ip_risk_classification' },
        { label: 'Score Confidence', prop: 'score_confidence' },
      ],
    },
    {
      title: 'SYNTHESIS & PROVENANCE',
      rows: [
        { label: 'IP Personality Summary', prop: 'ip_personality' },
      ],
    },
  ];

  let bodyHtml = '';
  sections.forEach(sec => {
    // Section Header
    bodyHtml += `
      <tr class="bg-surface-container-high/30">
        <td colspan="${observations.length + 1}" class="p-2.5 font-mono text-[10px] font-bold text-primary uppercase tracking-wider">
          ${sec.title}
        </td>
      </tr>
    `;

    sec.rows.forEach(r => {
      bodyHtml += `
        <tr class="hover:bg-surface-container/30 transition-colors">
          <td class="p-2.5 font-mono text-xs text-outline border-r border-surface-container/60">
            ${r.label}
          </td>
      `;
      observations.forEach(obs => {
        let valHtml = '';
        if (r.format) {
          valHtml = r.format(obs);
        } else {
          const val = obs[r.prop];
          valHtml = val !== null && val !== undefined && val !== '' ? String(val) : '<span class="text-outline">UNKNOWN</span>';
        }
        bodyHtml += `<td class="p-2.5 font-mono text-xs text-on-surface-variant">${valHtml}</td>`;
      });
      bodyHtml += `</tr>`;
    });
  });

  tbody.innerHTML = bodyHtml;
}

function renderComparisonStatistics(stats) {
  const container = document.getElementById('comp-stats-container');
  if (!container) return;

  const highestTrust = stats.highest_trust_score || {};
  const lowestTrust = stats.lowest_trust_score || {};
  const highestRisk = stats.highest_ip_risk_score || {};
  const lowestRisk = stats.lowest_ip_risk_score || {};
  const https = stats.https_adoption || {};
  const anon = stats.anonymizer_detections || {};

  container.innerHTML = `
    <div class="p-3 rounded-lg bg-surface-container-lowest/80 border border-surface-container flex flex-col gap-1">
      <span class="text-[10px] font-mono text-outline uppercase tracking-wider font-semibold">Highest Trust Score</span>
      <span class="text-sm font-bold text-tertiary font-mono">${highestTrust.score !== null && highestTrust.score !== undefined ? `${highestTrust.score}/100` : 'N/A'}</span>
      <span class="text-[11px] text-outline truncate">${highestTrust.domain || 'None'}</span>
    </div>
    <div class="p-3 rounded-lg bg-surface-container-lowest/80 border border-surface-container flex flex-col gap-1">
      <span class="text-[10px] font-mono text-outline uppercase tracking-wider font-semibold">Lowest Trust Score</span>
      <span class="text-sm font-bold text-amber-400 font-mono">${lowestTrust.score !== null && lowestTrust.score !== undefined ? `${lowestTrust.score}/100` : 'N/A'}</span>
      <span class="text-[11px] text-outline truncate">${lowestTrust.domain || 'None'}</span>
    </div>
    <div class="p-3 rounded-lg bg-surface-container-lowest/80 border border-surface-container flex flex-col gap-1">
      <span class="text-[10px] font-mono text-outline uppercase tracking-wider font-semibold">Highest IP Risk</span>
      <span class="text-sm font-bold text-error font-mono">${highestRisk.score !== null && highestRisk.score !== undefined ? `${highestRisk.score}/100` : 'N/A'}</span>
      <span class="text-[11px] text-outline truncate">${highestRisk.domain || 'None'}</span>
    </div>
    <div class="p-3 rounded-lg bg-surface-container-lowest/80 border border-surface-container flex flex-col gap-1">
      <span class="text-[10px] font-mono text-outline uppercase tracking-wider font-semibold">Lowest IP Risk</span>
      <span class="text-sm font-bold text-tertiary font-mono">${lowestRisk.score !== null && lowestRisk.score !== undefined ? `${lowestRisk.score}/100` : 'N/A'}</span>
      <span class="text-[11px] text-outline truncate">${lowestRisk.domain || 'None'}</span>
    </div>
    <div class="p-3 rounded-lg bg-surface-container-lowest/80 border border-surface-container flex flex-col gap-1 col-span-2">
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span class="text-[10px] font-mono text-outline block">Common ASN</span>
          <span class="font-mono text-on-surface font-medium">${stats.common_asn || 'No common value detected.'}</span>
        </div>
        <div>
          <span class="text-[10px] font-mono text-outline block">Common Organization</span>
          <span class="font-mono text-on-surface font-medium truncate block">${stats.common_organization || 'No common value detected.'}</span>
        </div>
        <div>
          <span class="text-[10px] font-mono text-outline block">Common Infrastructure</span>
          <span class="font-mono text-on-surface font-medium">${stats.common_infrastructure_type || 'No common value detected.'}</span>
        </div>
        <div>
          <span class="text-[10px] font-mono text-outline block">Common Country</span>
          <span class="font-mono text-on-surface font-medium">${stats.common_country || 'No common value detected.'}</span>
        </div>
      </div>
    </div>
    <div class="p-3 rounded-lg bg-surface-container-lowest/80 border border-surface-container flex items-center justify-between col-span-2">
      <div>
        <span class="text-[10px] font-mono text-outline block">HTTPS Transport Adoption</span>
        <span class="font-mono text-xs font-bold text-tertiary">${https.formatted || 'N/A'}</span>
      </div>
      <div>
        <span class="text-[10px] font-mono text-outline block">Anonymizers / Proxies</span>
        <span class="font-mono text-xs font-bold ${anon.total_anonymizers > 0 ? 'text-error' : 'text-outline'}">${anon.total_anonymizers || 0} Detected</span>
      </div>
    </div>
  `;
}

function renderDifferenceHighlights(diffs) {
  const container = document.getElementById('comp-differences-container');
  if (!container) return;

  container.innerHTML = '';
  if (!diffs || diffs.length === 0) {
    container.innerHTML = `<div class="text-xs text-outline font-mono italic">No distinct differences detected.</div>`;
    return;
  }

  diffs.forEach(d => {
    const item = document.createElement('div');
    item.className = 'flex items-start gap-2 p-2.5 rounded-lg bg-surface-container-lowest/70 border border-surface-container text-xs text-on-surface leading-snug';
    item.innerHTML = `
      <span class="material-symbols-outlined text-secondary text-[16px] shrink-0 mt-0.5">insights</span>
      <span>${d}</span>
    `;
    container.appendChild(item);
  });
}

function renderComparisonMap(mapPoints) {
  const mapBadge = document.getElementById('comp-map-count-badge');
  if (mapBadge) {
    mapBadge.textContent = `${mapPoints.length} Coordinate Point${mapPoints.length !== 1 ? 's' : ''}`;
  }

  const mapContainer = document.getElementById('comp-map');
  if (!mapContainer) return;

  // Initialize Leaflet if not yet created
  if (!window.compMapInstance) {
    window.compMapInstance = L.map('comp-map', {
      zoomControl: true,
      attributionControl: true,
      scrollWheelZoom: false,
    }).setView([20.0, 0.0], 2);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      subdomains: ['a', 'b', 'c'],
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
    }).addTo(window.compMapInstance);

    window.compMarkersLayer = L.featureGroup().addTo(window.compMapInstance);
  }

  if (window.compMarkersLayer) {
    window.compMarkersLayer.clearLayers();
  }

  if (mapPoints.length === 0) {
    window.compMapInstance.setView([20.0, 0.0], 2);
    return;
  }

  mapPoints.forEach(pt => {
    const customIcon = L.divIcon({
      className: 'comp-map-marker',
      html: `
        <div style="background: rgba(0, 210, 255, 0.9); width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #00d2ff;"></div>
      `,
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    });

    const marker = L.marker([pt.latitude, pt.longitude], { icon: customIcon });
    marker.bindPopup(`
      <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #dfe2ee; background: #0f131c; padding: 6px; border-radius: 6px;">
        <strong style="color: #a5e7ff; font-size: 12px;">${pt.domain}</strong><br/>
        <span>${pt.city || ''}, ${pt.country || ''}</span><br/>
        <span>IP: ${pt.resolved_ip}</span><br/>
        <span style="color: #69f6b9;">Trust: ${pt.trust_score !== null ? pt.trust_score : 'N/A'}</span> | 
        <span style="color: #ffb4ab;">Risk: ${pt.risk_score !== null ? pt.risk_score : 'N/A'}</span>
      </div>
    `);
    window.compMarkersLayer.addLayer(marker);
  });

  try {
    window.compMapInstance.fitBounds(window.compMarkersLayer.getBounds().pad(0.2));
  } catch (err) {
    console.debug('Map fitBounds fallback:', err);
  }

  setTimeout(() => {
    window.compMapInstance.invalidateSize();
  }, 100);
}

function resetComparisonAIView() {
  const idleEl = document.getElementById('comp-ai-idle');
  const loadingEl = document.getElementById('comp-ai-loading');
  const errorEl = document.getElementById('comp-ai-error');
  const resultEl = document.getElementById('comp-ai-result');
  const btnEl = document.getElementById('btn-explain-comparison-ai');
  const iconEl = document.getElementById('comp-ai-btn-icon');
  const labelEl = document.getElementById('comp-ai-btn-label');

  if (idleEl) idleEl.classList.remove('hidden');
  if (loadingEl) loadingEl.classList.add('hidden');
  if (errorEl) errorEl.classList.add('hidden');
  if (resultEl) resultEl.classList.add('hidden');

  if (btnEl) btnEl.disabled = false;
  if (iconEl) iconEl.textContent = 'auto_awesome';
  if (labelEl) labelEl.textContent = 'Explain Comparison with AI';

  window._isExplainingComparisonAI = false;
}

async function triggerComparisonAIExplanation() {
  if (window._isExplainingComparisonAI) return;
  if (!window.currentComparisonResult || !window.currentComparisonResult.observations) {
    alert('Please run a comparison first.');
    return;
  }

  const idleEl = document.getElementById('comp-ai-idle');
  const loadingEl = document.getElementById('comp-ai-loading');
  const errorEl = document.getElementById('comp-ai-error');
  const errorMsgEl = document.getElementById('comp-ai-error-msg');
  const resultEl = document.getElementById('comp-ai-result');
  const btnEl = document.getElementById('btn-explain-comparison-ai');
  const iconEl = document.getElementById('comp-ai-btn-icon');
  const labelEl = document.getElementById('comp-ai-btn-label');

  window._isExplainingComparisonAI = true;

  if (idleEl) idleEl.classList.add('hidden');
  if (errorEl) errorEl.classList.add('hidden');
  if (resultEl) resultEl.classList.add('hidden');
  if (loadingEl) loadingEl.classList.remove('hidden');

  if (btnEl) btnEl.disabled = true;
  if (iconEl) iconEl.textContent = 'progress_activity';
  if (labelEl) labelEl.textContent = 'Analyzing...';

  try {
    const res = await fetch(`${API_BASE}/api/compare/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comparison: window.currentComparisonResult }),
    });

    const data = await res.json();

    if (!res.ok || data.status === 'error') {
      if (loadingEl) loadingEl.classList.add('hidden');
      if (errorEl) errorEl.classList.remove('hidden');
      if (errorMsgEl) {
        errorMsgEl.textContent = data.summary || data.error || 'AI comparison unavailable. Deterministic comparison remains fully available.';
      }
      return;
    }

    if (loadingEl) loadingEl.classList.add('hidden');
    if (resultEl) resultEl.classList.remove('hidden');

    setText('comp-ai-summary-text', data.summary || 'Summary unavailable.');
    setText('comp-ai-infra-text', data.infrastructure_comparison || 'Infrastructure comparison unavailable.');
    setText('comp-ai-sec-text', data.security_comparison || 'Security comparison unavailable.');
    setText('comp-ai-takeaway-text', data.takeaway || 'Takeaway guidance unavailable.');
    setText('comp-ai-limitations-text', data.limitations || 'AI comparison interprets empirical telemetry. Deterministic classifications remain authoritative.');

    if (labelEl) labelEl.textContent = 'Re-explain';
    if (iconEl) iconEl.textContent = 'refresh';

  } catch (err) {
    console.error('AI comparison error:', err);
    if (loadingEl) loadingEl.classList.add('hidden');
    if (errorEl) errorEl.classList.remove('hidden');
    if (errorMsgEl) {
      errorMsgEl.textContent = `AI request failed: ${err.message}. Deterministic comparison is fully operational.`;
    }
  } finally {
    window._isExplainingComparisonAI = false;
    if (btnEl) btnEl.disabled = false;
  }
}

async function exportComparisonDataset(format = 'csv') {
  if (!window.currentComparisonResult || !window.currentComparisonResult.observations) {
    alert('Please execute comparison before exporting.');
    return;
  }

  const btnId = format === 'json' ? 'btn-export-comp-json' : 'btn-export-comp-csv';
  const btnEl = document.getElementById(btnId);
  const origHtml = btnEl ? btnEl.innerHTML : '';

  if (btnEl) {
    btnEl.disabled = true;
    btnEl.innerHTML = `<span class="material-symbols-outlined text-[15px] animate-spin">progress_activity</span><span>Exporting...</span>`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/compare/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        observations: window.currentComparisonResult.observations,
        format: format,
      }),
    });

    if (!res.ok) {
      throw new Error(`Export failed with status ${res.status}`);
    }

    const fallbackName = format === 'json' ? 'IP_PULSE_Comparison.json' : 'IP_PULSE_Comparison.csv';
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

    showExportToast(`Downloaded comparison dataset: ${downloadFilename}`);
  } catch (err) {
    console.error('Export error:', err);
    showExportToast(`Export failed: ${err.message}`, true);
  } finally {
    if (btnEl) {
      btnEl.disabled = false;
      btnEl.innerHTML = origHtml;
    }
  }
}

// Global exports for investigation workspace
window.loadInvestigationWorkspace = loadInvestigationWorkspace;
window.updateComparisonSelectionUI = updateComparisonSelectionUI;
window.openCandidateModal = openCandidateModal;
window.closeCandidateModal = closeCandidateModal;
window.setCandidateFilter = setCandidateFilter;
window.filterCandidateList = filterCandidateList;
window.toggleCandidateSelection = toggleCandidateSelection;
window.removeComparisonItem = removeComparisonItem;
window.addCurrentScanToComparison = addCurrentScanToComparison;
window.clearComparisonSelection = clearComparisonSelection;
window.runInvestigationComparison = runInvestigationComparison;
window.triggerComparisonAIExplanation = triggerComparisonAIExplanation;
window.exportComparisonDataset = exportComparisonDataset;
