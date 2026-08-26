# Live Demonstration Script & Guide

This script provides a practical, step-by-step demonstration walkthrough for presenting the **IP Address Tracker & Geolocation Tool** during an oral examination or live project evaluation.

---

## DEMO STEP 1: Launch Application

- **What to do:** Open PowerShell terminal, ensure virtual environment is active, and run:
  ```bash
  python app.py
  ```
- **What to say:** "Good morning/afternoon. I will now demonstrate our Python-based IP Address Tracker & Geolocation Tool. I am launching the desktop console by executing `python app.py`."
- **What to point at:** The main desktop application window (`IP PULSE`) opening cleanly with its dark slate interface.

---

## DEMO STEP 2: Explain Dashboard Interface Layout

- **What to do:** Keep the application on the **DASHBOARD** tab.
- **What to say:** "The application opens to the main intelligence console. At the top is our target search bar. In the upper right corner, the green status indicator shows `SYSTEM ONLINE`. The left sidebar allows seamless navigation between Dashboard, History, Field Test, and Analytics."
- **What to point at:** Point to the top search bar, the `● SYSTEM ONLINE` header badge, and the left sidebar navigation buttons.

---

## DEMO STEP 3: Enter Target Domain Name

- **What to do:** Click inside the **TARGET INTEL** text input box and type: `google.com`.
- **What to say:** "I will start by analyzing a standard public domain name: `google.com`."
- **What to point at:** The text input box containing `google.com`.

---

## DEMO STEP 4: Trigger Lookup Execution

- **What to do:** Click the **ANALYZE** button (or press `Enter` on your keyboard).
- **What to say:** "When I click ANALYZE, the software validates the domain syntax, resolves IPv4 and IPv6 addresses via DNS, applies our deterministic IP selection rule, and queries the HTTPS geolocation provider."
- **What to point at:** The animated loading indicator (`● ANALYZING NETWORK & GEOLOCATION DATA...`) showing non-blocking background execution.

---

## DEMO STEP 5: Explain Results & Summary Cards

- **What to do:** Scroll through the newly rendered result view.
- **What to say:** "The lookup completed in approximately 108 milliseconds. At the top, three summary cards highlight our target IP (`142.250.190.46`), Location (`Mountain View, United States`), and Network Owner (`Google LLC`)."
- **What to point at:** Point to the status badge (`● STATUS: SUCCESS`), the 3 summary cards, and the execution timing panel showing DNS time and API time.

---

## DEMO STEP 6: Demonstrate OpenStreetMap Visualization

- **What to do:** Scroll to the **GEOGRAPHIC LOCATION MAP** section embedded in the result view.
- **What to say:** "Here, the application renders interactive OpenStreetMap tiles centered on the target's registry coordinates. We can zoom and pan using the mouse. Above the map, a clear disclaimer note emphasizes that this location represents approximate network registry associations, not GPS-level tracking."
- **What to point at:** Point to the map tile, the marker labeled `[142.250.190.46] Approximate IP Location`, and the disclaimer header notice.

---

## DEMO STEP 7: Open History & Demonstrate Persistence

- **What to do:** Click **HISTORY** on the left sidebar navigation.
- **What to say:** "Next, let's navigate to the History view. Every lookup is automatically saved to a local SQLite database (`data/ip_tracker.db`) using parameterized SQL queries. Clicking any row displays full details in the inspection pane below."
- **What to point at:** Point to the Treeview history table, the latest `google.com` entry at the top, and the record details pane.

---

## DEMO STEP 8: Demonstrate History Controls & Safety

- **What to do:** Click a row in history, point to the **DELETE SELECTED** and **CLEAR HISTORY** buttons (do not clear history).
- **What to say:** "The history interface includes controls to refresh records, delete selected entries, or clear history. Destructive actions require explicit confirmation dialogs to prevent accidental data loss."
- **What to point at:** Point to the control buttons in the top header bar of the History view.

---

## DEMO STEP 9: Open Field Test Tab

- **What to do:** Click **FIELD TEST** on the left sidebar navigation.
- **What to say:** "In Phase 9, we developed a controlled research module to test a predefined sample of 50 public websites across 11 categories loaded from `websites.csv`."
- **What to point at:** Point to the header stating `Dataset Ready: 50 predefined websites loaded` and the `START FIELD TEST` button.

---

## DEMO STEP 10: Open Analytics Dashboard

- **What to do:** Click **ANALYTICS** on the left sidebar navigation.
- **What to say:** "Navigating to the Analytics tab, our Phase 10 data engine processes the field test observations and computes descriptive statistics. At the top, KPI summary cards display total observations (50 sites), overall success rate (98% DNS resolution), median lookup time, and unique countries."
- **What to point at:** Point to the 4 top KPI summary cards and the Descriptive Performance Metrics table.

---

## DEMO STEP 11: Display Research Chart Gallery

- **What to do:** Click the dropdown in the **RESEARCH CHART GALLERY** section and switch between charts (e.g. `country_distribution.png`, `dns_response_time.png`).
- **What to say:** "The analytics view includes a chart gallery previewing 7 publication plots generated via Matplotlib. For example, selecting `dns_response_time.png` shows our DNS resolution latency distribution, with a median resolution time of 22.27 milliseconds."
- **What to point at:** Point to the chart selector dropdown and the displayed dark-themed histogram image.

---

## DEMO STEP 12: Conclude Demonstration with Key Limitation

- **What to do:** Return to the main window or conclude standing at the console.
- **What to say:** "In summary, the application demonstrates high-performance DNS resolution, IP geolocation, interactive mapping, and batch field testing. As an academic conclusion, we emphasize that IP geolocation maps regional network infrastructure registry data rather than physical user locations. This completes our demonstration. Thank you, and I welcome your questions."
- **What to point at:** Point to the overall application window and open the floor for viva questions.
