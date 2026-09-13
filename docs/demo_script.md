# IP PULSE: Live Examination Demonstration Script

**Project Title:** IP PULSE — Autonomous IP Intelligence, Geolocation & Website Risk Analysis Platform  
**Target Environment:** Localhost Web Server (`http://127.0.0.1:5000` via Python Flask)  
**UI Interface:** Stitch Obsidian Dark Glassmorphic Web Console  
**Target Audience:** Academic Viva Examiners, External Evaluators, Faculty Committee  
**Total Steps:** 12 Guided Practical Steps  
**Demonstration Time:** Approximately 10–12 Minutes

---

## DEMO STEP 1: System Initialization & Server Launch

- **Goal:** Demonstrate clean, dependency-free server startup and verification of backend services.
- **Action:** Open PowerShell or Command Prompt in the project root and run:
  ```powershell
  python app.py
  ```
  Observe the startup log confirming port 5000 binding and SQLite database initialization. Open browser to `http://127.0.0.1:5000`.
- **Spoken Script:**
  > "Good morning, respected examiners. I will begin by starting the IP PULSE platform. By executing `python app.py`, our Flask application initializes the local SQLite database schema, binds security headers, and launches the local HTTP service on port 5000. Navigating to `http://localhost:5000`, the Stitch Obsidian Dark console loads instantaneously."
- **What to Point At:**
  - The terminal output displaying server startup and database connection.
  - The browser window rendering the dark obsidian interface.
  - The pulsing green `● SYSTEM ONLINE` status indicator in the top right navigation bar.

---

## DEMO STEP 2: Dashboard Overview & Visual Architecture

- **Goal:** Orient examiners with the single-pane-of-glass layout, theme system, and navigation hierarchy.
- **Action:** Mouse over the navigation tabs (`Dashboard`, `Compare`, `History`, `Field Study`, `Analytics`) and show the target input search bar.
- **Spoken Script:**
  > "The user interface is engineered as an Obsidian Dark Glassmorphic console. The primary view provides a unified reconnaissance console. At the top, we have our global Target Intelligence search bar. On the left navigation, users can seamlessly transition between single-target Dashboard, dual-target Comparison, local SQLite History, Empirical Field Study, and Research Analytics. Notice the real-time telemetry counters tracking total lifetime lookups and system uptime."
- **What to Point At:**
  - Top navigation bar with branding logo, active view links, and system status chip.
  - The central glowing input box with placeholder `Enter domain name or IPv4/IPv6 address...`.
  - Quick action example pills below the input (`google.com`, `cloudflare.com`, `1.1.1.1`).

---

## DEMO STEP 3: Single Target Intelligence Execution

- **Goal:** Demonstrate input validation, normalization, and asynchronous multi-engine execution.
- **Action:** Type `google.com` into the search box and press `Enter` (or click the glowing `ANALYZE` button).
- **Spoken Script:**
  > "I will now initiate an intelligence scan on a standard public domain: `google.com`. Notice that even if I typed `https://google.com/search`, our input normalizer cleans the string to the bare FQDN `google.com` and verifies its syntax. When I submit the query, an asynchronous AJAX request triggers our backend pipeline without any browser page reload."
- **What to Point At:**
  - The input text normalization.
  - The loading spinner state displaying `Querying DNS resolvers, TLS certificates & geolocation telemetry...`.
  - The rapid resolution time (typically under 300ms) displayed in the performance badge.

---

## DEMO STEP 4: Core Network & Interactive Leaflet Geolocation

- **Goal:** Showcase resolved IP telemetry, ASN ownership, and coordinate mapping with academic disclaimers.
- **Action:** Scroll down to the resolved IP metadata cards and interact with the Leaflet.js OpenStreetMap map view.
- **Spoken Script:**
  > "The lookup is complete. At the top of the results, three primary intelligence cards display the resolved primary IPv4 address (`142.250.190.46`), the geographic allocation (`Mountain View, California, United States`), and the Autonomous System routing entity (`AS15169 Google LLC`). Directly adjacent is an interactive Leaflet map centered precisely on these coordinates. Notice the prominent academic disclaimer: 'Location reflects public network registry allocation, not real-time GPS device tracking.' This ensures users understand the technical reality of IP geolocation."
- **What to Point At:**
  - The Resolved IP badge showing IPv4 classification.
  - The Organization card displaying AS15169 and Google LLC.
  - The Leaflet map marker and the disclaimer text directly above the map viewport.

---

## DEMO STEP 5: Deep DNS Dissection & Website Security Audit

- **Goal:** Present multi-record DNS resolution and active TLS/SSL cryptographic inspection.
- **Action:** Expand the **DNS Records** table and the **Website Security Intelligence** panel.
- **Spoken Script:**
  > "Looking into the technical infrastructure, our DNS engine queried the authoritative nameservers and extracted all forward and administrative records: A records, IPv6 AAAA records, Mail Exchanger (MX) servers, and Authoritative Nameservers (NS). Next, examining the Website Security panel, our scanner performed an active TLS handshake on port 443. We observe that `google.com` is utilizing modern TLS 1.3 with a high-strength AES cipher suite. The certificate validity window shows over 60 days remaining."
- **What to Point At:**
  - The DNS records grid showing A, AAAA, MX, and NS rows.
  - The TLS Certificate card with green `VALID` badge, issuer details, and expiration countdown.
  - The 6 HTTP Security Header chips showing compliance status for HSTS, CSP, and X-Content-Type-Options.

---

## DEMO STEP 6: Deterministic Dual-Score Trust & Risk Engine

- **Goal:** Explain the mathematical formulation and auditable factor breakdown of the scoring engine.
- **Action:** Point to the dual circular SVG gauge meters displaying Trust Score (e.g., 85/100) and Risk Score (e.g., 15/100).
- **Spoken Script:**
  > "Here is one of our key algorithmic contributions: the Deterministic Dual-Score Engine. You will notice the Trust Score is 85 and the Risk Score is 15. In our architecture, Trust plus Risk strictly equals 100 at all times. This is not an arbitrary machine-learning estimate; it is calculated using five explicit factor vectors. Below the gauges, the breakdown bars show that `google.com` earned +25 points for valid TLS 1.3, +10 points for verified Enterprise ASN reputation, but had a slight deduction due to missing Content-Security-Policy on the apex domain."
- **What to Point At:**
  - The glowing emerald Trust Score gauge and the complementary crimson Risk Score gauge.
  - The mathematical equality note: `Trust + Risk = 100`.
  - The 5 factor breakdown progress bars with exact point values and human-readable explanations.

---

## DEMO STEP 7: IP Personality Archetype & Behavioral Synthesis

- **Goal:** Show heuristic infrastructure profiling that transforms raw IPs into operational categories.
- **Action:** Highlight the **IP Personality** card on the dashboard.
- **Spoken Script:**
  > "Raw network attributes can be difficult to interpret at a glance. Our IP Personality module analyzes the combination of ASN ownership, reverse DNS PTR records, and open service ports to categorize the host. In this case, `google.com` is classified as 'Cloud Hyperscaler & Search Core Infrastructure'. The behavioral tag matrix informs the investigator that this node operates Anycast multi-homed routing, distributed global caching, and high-availability load balancers."
- **What to Point At:**
  - The distinctive archetype badge (`Cloud Hyperscaler`).
  - The behavioral feature chips (`Anycast Routing`, `Multi-Region Cluster`, `Encrypted In-Flight`).
  - The concise summary paragraph explaining the infrastructure's operational profile.

---

## DEMO STEP 8: Explainable AI (XAI) Intelligence Layer

- **Goal:** Demonstrate natural language narrative generation, offline rule fallback, and zero score hallucination.
- **Action:** Click the **AI Intelligence Brief** accordion or toggle.
- **Spoken Script:**
  > "To make this intelligence actionable for non-technical stakeholders, IP PULSE incorporates an Explainable AI layer. Powered by Google Gemini with an automatic local rule-based fallback, the system translates the low-level metrics into a structured 4-part intelligence brief: Executive Summary, Infrastructure Context, Risk Drivers, and Actionable Remediation. Crucially, the AI is constrained by design: it never computes or alters numerical scores, completely preventing score hallucination."
- **What to Point At:**
  - The AI provider badge (e.g., `Gemini Pro 1.5` or `Local Deterministic Fallback`).
  - The four structured narrative sections: Executive Summary, Infrastructure, Drivers, and Recommendations.
  - The remediation checklist detailing practical steps for administrators.

---

## DEMO STEP 9: Side-by-Side Target Comparison Workspace

- **Goal:** Demonstrate dual-target differential reconnaissance and delta metric calculation.
- **Action:** Click the **Compare** tab on the top navigation. Enter `google.com` in Target A and `cloudflare.com` in Target B, then click **COMPARE TARGETS**.
- **Spoken Script:**
  > "Now I will demonstrate our Investigation Workspace by navigating to the Compare tab. This allows an analyst to perform differential security audits between two network targets. In Target A, we enter `google.com`, and in Target B, `cloudflare.com`. Clicking Compare executes parallel lookups and renders side-by-side comparative telemetry. Notice the delta indicators: the system computes exact numerical deltas for Trust, Risk, latency, and contrasts their TLS cipher suites and security header policies."
- **What to Point At:**
  - The dual-column layout displaying Target A and Target B cards.
  - The central Delta column showing $\Delta \text{ Trust}$, $\Delta \text{ Latency}$, and $\Delta \text{ Headers}$.
  - The comparative advantage badges (e.g., green checkmarks indicating superior header enforcement).

---

## DEMO STEP 10: Empirical Research Field Study Console

- **Goal:** Show the research methodology, experimental dataset, and scientific data collection status.
- **Action:** Click the **Field Study** tab on the top navigation.
- **Spoken Script:**
  > "Beyond single-target lookups, IP PULSE serves as an empirical research platform. In the Field Study tab, we formulated a 50-website experimental protocol across 11 industry verticals, loaded from `websites.csv`. In our verified SQLite database, we currently have 7 completed, authenticated empirical observations. As shown in the status badge, the collection status is transparently reported as 7 of 50 completed. Our research methodology strictly reports authentic empirical observations rather than synthesizing uncollected records."
- **What to Point At:**
  - The 50-target protocol table with category classifications (Search, Tech, Media, Government).
  - The progress meter displaying `7 / 50 Observations Completed (14.0%)`.
  - The empirical observations table showing live recorded DNS latencies and TLS statuses.

---

## DEMO STEP 11: Analytics Dashboard & Research Visualizations

- **Goal:** Demonstrate historical telemetry aggregation, statistical calculations, and responsive Chart.js visual distribution.
- **Action:** Click the **Analytics** tab on the top navigation.
- **Spoken Script:**
  > "Navigating to the Analytics tab, our data engine aggregates empirical observations into statistical metrics and interactive Chart.js visualizations. The top KPI cards show total observations, mean Trust score of 85.0, mean Risk score of 15.0, and 100% DNS resolution success. Looking at the charts below, the Protocol Distribution shows 85.7% IPv4 and 14.3% IPv6 adoption. The Geographic Distribution highlights significant infrastructure concentration: 42.9% in the United States and 28.6% in Canada, with Cloudflare AS13335 representing the most prominent network operator."
- **What to Point At:**
  - The 4 top KPI summary metric cards (Total Lookups, Mean Trust, Mean Risk, Protocol Split).
  - The Protocol Distribution donut chart (hover over slices to show tooltips).
  - The Country Distribution bar chart and the Risk Score Histogram.

---

## DEMO STEP 12: Data Persistence, Export & Demonstration Conclusion

- **Goal:** Verify SQLite storage integrity, data export capabilities, and summarize defense highlights.
- **Action:** Click the **History** tab to show persisted entries, click **EXPORT JSON** (or CSV), and return to the main dashboard.
- **Spoken Script:**
  > "Finally, we demonstrate data persistence and export. Every query is recorded in our SQLite database (`data/ip_tracker.db`) using parameterized SQL queries to prevent injection. Analysts can search past lookups or export the complete dataset in structured JSON or CSV format for external SIEM ingestion. In conclusion, IP PULSE provides an end-to-end, deterministic, explainable, and thoroughly tested intelligence platform with 214 passing automated tests. This completes my live demonstration, and I welcome your questions."
- **What to Point At:**
  - The History table listing recent scans with timestamps and IP addresses.
  - The Export button generating and downloading the structured data payload.
  - The final clean status of the system console.
