# IP Address Tracker & Geolocation Tool

## Overview
A Python-based application designed for resolving website domains to public IP addresses, retrieving approximate IP geolocation and network information, storing lookup results locally, visualizing geographic information, and conducting a structured field study across 50 websites.

## Project Purpose
This project is a College Semester Field Project focused on IP/DNS analysis and approximate geolocation. It evaluates DNS resolution behaviors, public IP address locations, network providers, and infrastructure distributions.

## Current Status
- **Current Phase:** Phase 6 — Database & Lookup History
- **Status:** Complete (Local SQLite database `data/ip_tracker.db`, parameterized SQL CRUD methods, and database tests implemented)
- **Primary Geolocation Provider:** `ipapi.co` (HTTPS, supports IPv4/IPv6)
- **Database Engine:** SQLite (built-in `sqlite3`, parameterized queries, persistent lookup history)
- **Master Reference:** [architecture.md](architecture.md)

### Deterministic IP Selection Rule
When a domain resolves to multiple IP addresses:
1. The **first valid IPv4 address** returned by DNS resolution is selected for geolocation.
2. If no IPv4 address is available, the **first valid IPv6 address** is selected.
3. All resolved IPv4 and IPv6 addresses are preserved in `resolved_addresses` for analysis.

## Technology Stack
- **Language:** Python 3 (3.14+)
- **Environment:** Virtual environment (`.venv`)
- **Database:** SQLite (`data/ip_tracker.db`)

## Getting Started

### 1. Environment Setup
Create and activate the virtual environment:
```bash
python -m venv .venv
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate
```

### 2. Configuration (Optional)
Copy configuration template:
```bash
cp .env.example .env
```
*(Free tier works up to 1,000 requests/day out of the box without an API key)*

### 3. Running Tests
Run the test suite:
```bash
python -m unittest discover -s tests
```

### 4. Running the Application
Execute the entry point script to run end-to-end lookup and view SQLite history:
```bash
python app.py
```

## Development Roadmap
Implementation proceeds strictly phase-by-phase according to [architecture.md](architecture.md):
- **Phase 1:** Development Environment (Complete)
- **Phase 2:** Input Validation (Complete)
- **Phase 3:** DNS Resolution (Complete)
- **Phase 4:** Geolocation Service (Complete)
- **Phase 5:** Integrated Lookup Engine (Complete)
- **Phase 6:** Database & History (Complete)
- **Phase 7:** GUI Development
- **Phase 8:** Map Visualization
- **Phase 9:** Field-Test Module (50 Websites)
- **Phase 10:** Data Analysis
- **Phase 11:** Charts & Dashboard Analytics
- **Phase 12:** Data Export
- **Phase 13:** Testing & Hardening
- **Phase 14:** Final Packaging
- **Phase 15:** Field Project Report
- **Phase 16:** Viva Preparation
