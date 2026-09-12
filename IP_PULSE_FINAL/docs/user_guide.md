# End-User Guide & Operating Manual

Welcome to the **IP Address Tracker & Geolocation Tool** user guide. This document provides step-by-step instructions for installing, configuring, and operating the `IP PULSE` Desktop Network Intelligence Console.

---

## 1. System Requirements & Installation

### Minimum Requirements
- **Operating System:** Windows 10/11, macOS 11+, or Linux (Ubuntu 20.04+)
- **Python:** Python 3.14+ (Python 3.10+ supported)
- **Memory:** 2 GB RAM (4 GB recommended)
- **Disk Space:** 200 MB free storage

### Installation Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/VishwaAdarsh/ip-address-tracker.git
   cd ip-address-tracker
   ```

2. **Set Up Python Virtual Environment:**
   ```bash
   # Create virtual environment
   python -m venv .venv

   # Activate virtual environment (Windows PowerShell):
   .\.venv\Scripts\Activate.ps1

   # Activate virtual environment (Linux/macOS):
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 2. API Configuration (Optional)

The application queries `ipapi.co` over secure HTTPS. By default, the free tier works out of the box (up to 1,000 requests/day).

If you have a dedicated API key, configure `.env`:
```bash
cp .env.example .env
```
Edit `.env` using any text editor:
```env
GEO_PROVIDER_NAME=ipapi.co
GEO_API_BASE_URL=https://ipapi.co
GEO_API_KEY=YOUR_GEO_API_KEY
GEO_API_TIMEOUT=5.0
```

---

## 3. Starting the Application

Launch the desktop interface by executing:
```bash
python app.py
```

The **IP PULSE Console** window will open (`1140x780` resolution).

---

## 4. Operating the Dashboard (Lookup Engine)

1. Navigate to the **DASHBOARD** tab via the left sidebar.
2. In the top search bar (**TARGET INTEL**), type any target domain or IP address:
   - Example Domain: `google.com`
   - Example IPv4: `8.8.8.8`
   - Example IPv6: `2001:4860:4860::8888`
3. Click **ANALYZE** or press `Enter` on your keyboard.
4. An animated status indicator (`● ANALYZING NETWORK & GEOLOCATION DATA...`) will display while the lookup processes asynchronously in the background.
5. Review the resulting intelligence panels:
   - **Status Badge:** Overall status (`● SUCCESS`, `● DNS FAILED`, etc.).
   - **Summary Cards:** Primary IP Address, Geolocation City/Country, Network Owner.
   - **Approximate IP Geolocation:** Country, Region, City, Coordinates, Timezone.
   - **Geographic Location Map:** Embedded OpenStreetMap tile with location marker.
   - **Network Details:** Organization, ISP, ASN, IPv4/IPv6 address lists.
   - **Performance Metrics:** DNS time, API time, and Total pipeline latency.

---

## 5. Viewing & Managing Lookup History

1. Click **HISTORY** on the left sidebar navigation.
2. The treeview table lists all past lookups stored in the local SQLite database (`data/ip_tracker.db`), ordered with the newest records at the top.
3. Click any row in the table to inspect full metadata in the bottom details pane.
4. **Action Buttons:**
   - **REFRESH:** Reloads history entries from SQLite.
   - **DELETE SELECTED:** Deletes the highlighted record (prompts for confirmation).
   - **CLEAR HISTORY:** Clears all historical records (prompts for explicit confirmation).

---

## 6. Interactive OpenStreetMap View

- The embedded map widget displays an OpenStreetMap tile centered on the target latitude and longitude.
- **Marker Text:** Shows `[Target] Approximate IP Location: City, Country`.
- **Navigation Controls:** Use mouse scroll to zoom in/out or click-and-drag to pan across the map.
- **Missing / Invalid Coordinates Handling:** If an IP address does not return valid coordinates, a clean dark panel displays: `MAP UNAVAILABLE - Coordinates were not provided for this IP lookup`.

---

## 7. Running 50-Website Field Experiments

1. Click **FIELD TEST** on the left sidebar.
2. The dataset header indicates `50 predefined websites loaded from data/field_test/websites.csv`.
3. Click **START FIELD TEST** to launch the batch test.
4. The progress bar updates in real time (`Progress: 17 / 50 (34%)`), and each finished website appears instantly in the live table.
5. Click **STOP / PAUSE** at any time to pause processing cleanly. Already completed records are preserved safely in `data/field_test/field_test_results.csv`.

---

## 8. Research Analytics & Chart Gallery

1. Click **ANALYTICS** on the left sidebar.
2. Review the top Key Performance Indicator (KPI) summary cards:
   - Total Observations (50 Sites)
   - Overall Success Rate (%)
   - Median Pipeline Latency (ms)
   - Unique Countries Identified
3. Inspect the **Descriptive Performance Metrics** table for Mean, Std Dev, Min, Median, P75, and Max timing values.
4. Select any plot from the **Research Chart Gallery** dropdown to view high-resolution dark-themed PNG charts (`country_distribution`, `ip_version_distribution`, `status_distribution`, `dns_response_time`, `total_response_time`, etc.).

---

## 9. Running Test Suite

Verify complete software integrity by running automated unit tests:
```bash
python -m unittest discover -s tests
```
All 54 unit and integration tests should pass with `OK`.

---

## 10. Troubleshooting & FAQ

| Problem | Cause | Solution |
|---|---|---|
| **GUI freezes or does not open** | Tkinter dependency missing | Ensure standard Python Tkinter is installed on your OS. |
| **"MAP COMPONENT UNLOADED"** | `tkintermapview` missing | Run `pip install tkintermapview>=1.30.0`. |
| **HTTP 429 Rate Limit Error** | Free API quota exceeded | Wait 1 hour or add a custom `GEO_API_KEY` in `.env`. |
| **"PermissionError: WinError 32"** | File handle locked | Ensure test background tasks finish before deleting test files. |
