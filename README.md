# IP Address Tracker & Geolocation Tool

## Overview
A Python-based application designed for resolving website domains to public IP addresses, retrieving approximate IP geolocation and network information, storing lookup results locally, visualizing geographic information, and conducting a structured field study across 50 websites.

## Project Purpose
This project is a College Semester Field Project focused on IP/DNS analysis and approximate geolocation. It evaluates DNS resolution behaviors, public IP address locations, network providers, and infrastructure distributions.

## Current Status
- **Current Phase:** Phase 3 — DNS Resolution
- **Status:** Complete (DNS resolution engine, timing, and unit tests implemented)
- **Master Reference:** [architecture.md](architecture.md)

## Technology Stack
- **Language:** Python 3 (3.14+)
- **Environment:** Virtual environment (`.venv`)

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

### 2. Running Tests
Run the test suite:
```bash
python -m unittest discover -s tests
```

### 3. Running the Application
Execute the entry point script to verify setup:
```bash
python app.py
```

## Development Roadmap
Implementation proceeds strictly phase-by-phase according to [architecture.md](architecture.md):
- **Phase 1:** Development Environment (Complete)
- **Phase 2:** Input Validation (Complete)
- **Phase 3:** DNS Resolution (Complete)
- **Phase 4:** Geolocation Service
- **Phase 5:** Integrated Lookup Engine
- **Phase 6:** Database & History
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
