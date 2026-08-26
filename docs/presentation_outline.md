# Presentation Outline & Slide Deck Structure

**Project Title:** Python-based IP Address Tracker & Geolocation Tool  
**Visual Theme:** Dark Slate Technical Console (`#0F172A` Slate 900, `#1E293B` Slate 800, `#0EA5E9` Sky Blue Accent)  
**Total Slides:** 15 Slides  

---

## SLIDE 1: Title Slide
- **Title:** Python-based IP Address Tracker & Geolocation Tool
- **Subtitle:** A Controlled Field Study of Domain Resolution, Public IP Geolocation, and Infrastructure Patterns Across 50 Websites
- **Student Details:** [Student Name] | Roll No: [Roll Number]
- **Department/College:** [Department Name], [College Name]
- **Guide:** [Teacher Name / Project Guide]

---

## SLIDE 2: Problem Statement
- **Key Challenges:**
  - Standard command-line tools (`nslookup`, `dig`) return raw network IPs without geographic context or persistent logging.
  - Lack of unified desktop tools combining input validation, socket DNS, HTTPS geolocation, SQLite history, and mapping.
  - Misconceptions surrounding IP geolocation accuracy vs. physical device location.
- **Solution:** A clean, 4-tier Python desktop application (`IP PULSE`) designed for single lookups and controlled batch field research.

---

## SLIDE 3: Project Objectives
1. **Engine Architecture:** Build modular Python engines for validation, DNS resolution, and geolocation.
2. **Persistence & Mapping:** Develop parameterized SQLite history storage and interactive OpenStreetMap visualization.
3. **Desktop Interface:** Create a responsive dark-themed GUI console utilizing non-blocking daemon threads.
4. **Field Study:** Execute a 50-website controlled research experiment, analyze timing statistics, and render publication plots.

---

## SLIDE 4: Technology Stack
- **Language:** Python 3 (3.14+)
- **Desktop GUI:** Tkinter / ttk (`gui/main_window.py`)
- **Map Visualization:** `tkintermapview` (`gui/map_view.py`)
- **Data Analysis:** `pandas`, `matplotlib`, `numpy` (`analysis/`)
- **Database Engine:** SQLite (`database/db.py`)
- **Networking:** Standard library `socket`, `urllib.request`

---

## SLIDE 5: System Architecture
```text
┌─────────────────────────────────────────────────────────┐
│              PRESENTATION LAYER (GUI Console)           │
│ ResultsView │ HistoryView │ FieldTestView │ AnalyticsView│
└────────────────────────────┬────────────────────────────┘
                             │ (Async Background Threads)
                             ▼
┌─────────────────────────────────────────────────────────┐
│               SERVICES ORCHESTRATION LAYER              │
│       lookup_service.py   │   field_test_service.py     │
└───────┬────────────────────┬────────────────────┬───────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ CORE ENGINES │     │ DATABASE     │     │ ANALYSIS     │
│ Validation   │     │ SQLite       │     │ Analyzer     │
│ DNS Resolver │     │ ip_tracker.db│     │ Visualizer   │
│ Geolocation  │     └──────────────┴─────┴──────────────┘
└──────────────┘
```

---

## SLIDE 6: Single Target Lookup Workflow
```text
User Input -> Validation -> Socket DNS -> IP Selection (1st IPv4) -> HTTPS Geolocation -> SQLite Log -> UI Cards & Map
```
- **Deterministic Rule:** Prefers 1st IPv4 address; falls back to 1st IPv6 address if no IPv4 exists.

---

## SLIDE 7: Desktop Console GUI (`IP PULSE`)
- **Design:** Modern dark slate theme (`#0F172A`).
- **Features:** Input search bar with keyboard `Enter` trigger, active loading state, status badges (`● SUCCESS`).
- **Cards:** 3 summary cards (Target IP, Geolocation, Network Owner) + detailed metadata section.
- **Responsiveness:** Non-blocking background threads ensure UI main loop never freezes.

---

## SLIDE 8: Interactive Map Visualization
- **Renderer:** Embedded OpenStreetMap tile renderer (`tkintermapview`).
- **Marker:** Interactive marker centered on target coordinates (`Lat, Lon`).
- **Safety:** Coordinate bounds validation (-90..90 lat, -180..180 lon) with clear fallback panel for missing/unreturned coordinates.
- **Disclaimer:** Prominent header notice: `* Location shown is an approximate IP geolocation and may not represent exact physical location.`

---

## SLIDE 9: Local SQLite History Storage
- **Database:** `data/ip_tracker.db` (`lookup_history` table).
- **Features:** Auto-saves completed lookups using parameterized SQL (`?`).
- **UI View:** `ttk.Treeview` table ordered by `timestamp DESC` with record inspection pane, delete selected, and clear history options.
- **Safety:** Explicit `finally: conn.close()` resource cleanup prevents Windows file handle locks.

---

## SLIDE 10: 50-Website Field Test Experiment
- **Dataset:** 50 predefined public websites across 11 categories (`data/field_test/websites.csv`).
- **Methodology:** Sequential execution paced at 0.5s intervals to respect API limits.
- **Data Integrity:** Raw observations saved to `data/field_test/field_test_results.csv`. Individual lookup failures (`DNS_FAILED`) preserved as empirical observations.

---

## SLIDE 11: Data Analysis & Research Plots
- **Statistics:** Descriptive metrics (mean, median, min, max, std, percentiles) computed via `pandas` & `numpy`.
- **7 Rendered Plots:**
  1. Top Geolocation Countries
  2. IPv4 vs. IPv6 Ratio
  3. Lookup Status Outcomes
  4. DNS Resolution Latency Histogram
  5. Geolocation API Latency Histogram
  6. Total Pipeline Latency Histogram
  7. Website Sample Category Distribution

---

## SLIDE 12: Empirical Research Findings
- **DNS Resolution Success Rate:** **98.0%** (49/50 domains resolved).
- **IPv4 Preference Ratio:** **98.0%** IPv4 (49/50) | 0.0% IPv6.
- **Median DNS Resolution Latency:** **22.27 ms** (Mean: 101.05 ms).
- **Median Geolocation API Latency:** **80.75 ms** (Mean: 256.55 ms).
- **Median Total Pipeline Latency:** **108.64 ms** (Mean: 358.00 ms).
- **Hosting Concentration:** United States represented 35 out of 50 target infrastructure registries.

---

## SLIDE 13: Technical & Sample Limitations
1. **Approximate Geolocation:** IP registry allocations, not GPS tracking.
2. **DNS & CDN Variability:** DNS answers change dynamically over time due to CDNs and load balancers.
3. **Purposive Sample:** 50 websites represent a convenience sample, not all global internet hosts.
4. **Skewed Latency:** Network timing is right-skewed; median is used as the primary central tendency metric.

---

## SLIDE 14: Future Scope & Enhancements
1. Multi-Provider Geolocation API Failover (ipinfo.io, MaxMind GeoIP2).
2. Autonomous System BGP route tracing.
3. Web application deployment using FastAPI and React.

---

## SLIDE 15: Conclusion & Academic Summary
- **Fulfillment:** 100% of master requirements in [architecture.md](../architecture.md) achieved.
- **Quality Assurance:** **54 unit/integration tests** passing (100% pass rate).
- **Core takeaway:** Unified desktop application delivering high-performance DNS resolution, IP geolocation, interactive mapping, and empirical field research capabilities.
