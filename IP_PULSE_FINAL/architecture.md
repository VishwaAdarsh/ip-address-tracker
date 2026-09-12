# Python-based IP Address Tracker & Geolocation Tool
## Project Architecture & Development Blueprint

**Project Type:** College Semester Field Project  
**Primary Language:** Python  
**Field Study:** 50 websites  
**Development Environment:** Antigravity 2.0  
**Document Purpose:** Master architecture and implementation reference

---

## 1. Project Overview

This project is a Python-based application for resolving website domains to public IP addresses, retrieving approximate IP geolocation and network information, storing lookup results, visualizing selected geographic information, and conducting a structured field study on 50 websites.

The application must be treated as an **IP/DNS analysis and approximate geolocation tool**, not as a people-tracking or exact-location system.

### Core workflow

```text
Domain / IP Input
        |
        v
Input Validation
        |
        +----------------------+
        |                      |
      Domain                   IP
        |                      |
        v                      |
    DNS Resolve                |
        |                      |
        +----------+-----------+
                   |
                   v
              IP Address
                   |
                   v
          Geolocation Service
                   |
                   v
             JSON Response
                   |
                   v
          Normalize / Validate
                   |
          +--------+--------+
          |        |        |
          v        v        v
        GUI     Database   Analysis
          |                 |
          v                 v
         Map              Charts
          |
          +--------+
                   |
                   v
              Export Data
```

---

# 2. Project Objectives

The final product must be able to:

1. Accept a domain name or IP address.
2. Validate the user input.
3. Resolve a domain name to a public IP address.
4. Support IPv4 and, where practical, IPv6.
5. Retrieve approximate IP geolocation information.
6. Retrieve available network information such as organization/ISP and ASN.
7. Display results in a professional GUI.
8. Show approximate geographic coordinates on a map.
9. Store lookup history locally.
10. Handle errors and missing information gracefully.
11. Process a controlled dataset of 50 websites.
12. Record field-test results in a structured format.
13. Analyze geographic and network patterns.
14. Generate charts/statistics from the field-test data.
15. Export collected data to CSV and, where useful, Excel.
16. Provide enough logging and documentation to reproduce the experiment.
17. Clearly communicate the limitations of IP geolocation.

---

# 3. Project Scope

## 3.1 In Scope

- Public domain DNS resolution
- Public IP address analysis
- IP validation
- IPv4/IPv6 handling
- IP geolocation through a legitimate API/service
- Approximate country, region, city, coordinates and timezone when available
- ASN and organization/network information when available
- Local lookup history
- 50-website field testing
- Data cleaning
- Statistical analysis
- Charts
- Map visualization
- CSV/Excel export
- Error handling
- Logging
- Documentation

## 3.2 Out of Scope

The application must not attempt to:

- determine a person's exact physical location;
- track a person's live movement;
- identify a person's home address;
- access private IP addresses without authorization;
- bypass authentication;
- hack or exploit servers;
- perform unauthorized network scanning;
- collect private user information;
- claim that an IP geolocation result is an exact physical server location.

---

# 4. Important Technical Assumptions

## 4.1 IP geolocation is approximate

The application must use wording such as:

> "Approximate IP geolocation"

rather than:

> "Exact location"

The result represents information associated with the network/IP database record. It may differ from the physical location of the website's infrastructure or user.

## 4.2 A domain does not necessarily map to one permanent IP

Modern websites can use:

- CDNs
- load balancers
- reverse proxies
- cloud infrastructure
- geographically distributed infrastructure
- multiple DNS records

Therefore, the software must not assume:

```text
one domain = one permanent server
```

## 4.3 Results are time-dependent

DNS and geolocation information can change.

Each field-test record should therefore contain a timestamp.

## 4.4 Missing information must remain missing

If the provider does not return a field, the software must store a clear null/empty value such as:

```text
N/A
```

It must never invent or estimate unavailable values.

---

# 5. High-Level System Architecture

```text
+----------------------------------------------------------+
|                     PRESENTATION LAYER                   |
|                                                          |
|  Main Window | Lookup Form | Results | History | Charts |
|  Map View    | Field Test  | Export   | Settings        |
+-------------------------------+--------------------------+
                                |
                                v
+----------------------------------------------------------+
|                     APPLICATION LAYER                    |
|                                                          |
|  Lookup Controller                                       |
|  Field-Test Controller                                  |
|  History Controller                                      |
|  Analysis Controller                                     |
|  Export Controller                                       |
+-------------------------------+--------------------------+
                                |
                                v
+----------------------------------------------------------+
|                       CORE SERVICES                      |
|                                                          |
|  Input Validator                                         |
|  DNS Resolver                                            |
|  IP Validator                                            |
|  Geolocation Client                                      |
|  Response Normalizer                                     |
|  Result Analyzer                                         |
|  Error Handler                                           |
+-------------------------------+--------------------------+
                                |
                 +--------------+--------------+
                 |                             |
                 v                             v
+----------------------------+   +--------------------------+
|      EXTERNAL SERVICES     |   |       DATA LAYER         |
|                            |   |                          |
| DNS / OS Resolver          |   | SQLite                   |
| IP Geolocation API         |   | CSV / Excel              |
| Map Provider / Map Library |   | Cached/History Data      |
+----------------------------+   +--------------------------+
```

---

# 6. Recommended Project Structure

The implementation should use a modular but practical structure.

```text
ip-geolocation-tool/
│
├── app.py
├── requirements.txt
├── README.md
├── ARCHITECTURE.md
├── .env
├── .gitignore
│
├── config/
│   └── settings.py
│
├── core/
│   ├── __init__.py
│   ├── validator.py
│   ├── dns_resolver.py
│   ├── geo_service.py
│   ├── normalizer.py
│   └── analyzer.py
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── models.py
│
├── gui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── results_view.py
│   ├── history_view.py
│   ├── field_test_view.py
│   ├── analytics_view.py
│   └── map_view.py
│
├── services/
│   ├── __init__.py
│   ├── lookup_service.py
│   ├── export_service.py
│   └── field_test_service.py
│
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── helpers.py
│
├── data/
│   ├── websites_50.csv
│   ├── field_test_results.csv
│   └── exports/
│
├── reports/
│   ├── analysis.py
│   └── charts/
│
├── logs/
│
└── tests/
    ├── test_validator.py
    ├── test_dns_resolver.py
    ├── test_normalizer.py
    └── test_analyzer.py
```

The structure can be simplified if a component is not needed. Do not create unnecessary files merely to make the project look complex.

---

# 7. Component Responsibilities

## 7.1 `app.py`

Application entry point.

Responsibilities:

- initialize the application;
- load configuration;
- initialize database;
- start the GUI;
- handle top-level startup errors.

It should not contain all business logic.

---

## 7.2 `core/validator.py`

Responsible for:

- domain validation;
- IPv4 validation;
- IPv6 validation;
- rejecting obviously invalid input;
- normalizing basic input format.

Example:

```text
google.com       -> valid domain
8.8.8.8         -> valid IPv4
2001:4860::8888 -> valid IPv6
hello            -> invalid
```

---

## 7.3 `core/dns_resolver.py`

Responsible for:

- resolving domain names;
- retrieving available IP addresses;
- distinguishing IPv4/IPv6 where possible;
- measuring DNS resolution time;
- handling DNS failures.

Do not silently convert a DNS failure into a fake result.

---

## 7.4 `core/geo_service.py`

Responsible for:

- communicating with the selected geolocation API;
- authenticating using an environment variable/API key when required;
- sending lookup requests;
- handling HTTP errors;
- handling timeouts;
- returning raw API data to the normalization layer.

API credentials must never be hard-coded in source code.

---

## 7.5 `core/normalizer.py`

The geolocation provider's JSON response must be converted into the application's standard internal format.

This protects the rest of the application from provider-specific field names.

Example internal record:

```text
ip
ip_version
country
country_code
region
city
latitude
longitude
timezone
organization
asn
isp
status
timestamp
```

---

## 7.6 `core/analyzer.py`

Responsible for:

- country frequency;
- region/city frequency;
- organization frequency;
- ASN frequency;
- IPv4/IPv6 distribution;
- successful/failed lookup rates;
- duplicate IP detection;
- response-time statistics;
- missing-data analysis.

---

# 8. Database Architecture

SQLite is the preferred local database for the project.

## 8.1 Lookup history table

Suggested fields:

```text
id
timestamp
input_value
input_type
domain
ip_address
ip_version
country
country_code
region
city
latitude
longitude
timezone
organization
isp
asn
dns_response_time_ms
api_response_time_ms
status
error_message
```

## 8.2 Field-test table

The field-test data should preserve experimental metadata.

Suggested fields:

```text
id
test_number
domain
category
timestamp
resolved_ip
ip_version
country
country_code
region
city
latitude
longitude
timezone
organization
isp
asn
dns_response_time_ms
api_response_time_ms
lookup_status
error_message
```

The exact schema may be adjusted after the API is selected.

---

# 9. API Integration Architecture

The API provider must be treated as an external dependency.

```text
Application
    |
    v
Geo Service
    |
    v
HTTP Request
    |
    v
Geolocation API
    |
    v
JSON
    |
    v
Response Normalizer
    |
    v
Internal Result Model
```

The rest of the application should not depend directly on provider-specific JSON field names.

This makes it possible to change providers later without rewriting the GUI or database logic.

---

# 10. Configuration and Secrets

Sensitive configuration must be stored outside the source code.

Example:

```text
.env
```

Possible variables:

```text
GEO_API_KEY=your_key_here
GEO_API_BASE_URL=provider_url
```

The actual API key must never be committed to Git or placed directly into Python source code.

The `.env` file must be included in `.gitignore`.

---

# 11. User Interface Architecture

The GUI should have a clean, professional student-project appearance.

## Main sections

### Dashboard

Contains:

- application title;
- domain/IP input;
- Analyze button;
- clear/reset button;
- optional My Public IP button;
- current status/loading indicator.

### Results

Display:

- input;
- resolved IP;
- IP version;
- country;
- region;
- city;
- organization/ISP;
- ASN;
- timezone;
- latitude;
- longitude;
- timestamp;
- response time;
- lookup status.

### Map

Display approximate coordinates when available.

The map must clearly indicate that the location is approximate.

### History

Display previous lookups in a table.

Potential actions:

- view;
- delete;
- clear history;
- search/filter.

### Field Test

Allow the project dataset of 50 websites to be loaded and processed.

Potential controls:

```text
Load 50 Websites
Run Test
Pause/Stop
View Results
Export
```

### Analytics

Display:

- total websites;
- successful lookups;
- failed lookups;
- country distribution;
- organization distribution;
- IPv4/IPv6 distribution;
- average response time;
- duplicate IP count.

---

# 12. Field-Test Methodology

The field test must be reproducible.

## Step 1 — Define sample

Select exactly 50 websites.

The list should contain categories rather than being an arbitrary collection.

Possible categories:

- Technology
- Search
- Social media
- E-commerce
- News
- Education
- Government
- Finance
- Entertainment
- Other popular websites

The final list must be documented before testing.

## Step 2 — Freeze the sample

Once the 50 websites are finalized, do not replace websites simply because a lookup fails.

Failures are valid observations.

## Step 3 — Establish test conditions

Record:

- test date;
- test time;
- network environment if relevant;
- API provider;
- software version;
- API/database version if available.

## Step 4 — Run the test

Each website follows the same process:

```text
Website
  |
  v
Validation
  |
  v
DNS Resolution
  |
  v
IP Address
  |
  v
Geolocation Lookup
  |
  v
Normalize Result
  |
  v
Store Result
```

## Step 5 — Preserve failures

Example statuses:

```text
SUCCESS
DNS_FAILED
GEOLOCATION_FAILED
TIMEOUT
INVALID_DOMAIN
API_ERROR
NO_DATA
```

Do not discard failed websites.

---

# 13. Multiple-IP Handling

A domain can resolve to multiple addresses.

The software should not silently choose an arbitrary address when multiple addresses are returned.

Preferred behavior:

```text
Domain
  |
  +--> IP 1
  |
  +--> IP 2
  |
  +--> IP 3
```

For the interactive lookup, the GUI may display all relevant resolved addresses or provide a clear primary-result rule.

For the field study, the methodology must explicitly define whether:

1. all returned IPs are analyzed, or
2. one deterministic IP-selection rule is used.

The final choice must be documented in the methodology.

---

# 14. Data Quality Rules

The application must follow these rules:

1. Never invent missing data.
2. Never claim exact physical location.
3. Preserve timestamps.
4. Preserve failed lookups.
5. Record the IP actually tested.
6. Record the API/service used.
7. Keep raw API data separate from normalized data when useful for debugging.
8. Avoid duplicate field-test records unless repeated testing is intentional.
9. Do not mix results from different test dates without recording the dates.
10. Do not manually alter experimental results without documenting the correction.

---

# 15. Analytics Requirements

The field-study analysis should include at least:

## Geographic analysis

- country count;
- country percentage;
- region/city frequency where meaningful;
- map distribution.

## Network analysis

- organization/ISP frequency;
- ASN frequency;
- duplicate IPs;
- infrastructure concentration.

## Technical analysis

- IPv4 vs IPv6;
- successful vs failed DNS resolution;
- successful vs failed geolocation;
- average/median response time;
- missing-field percentage.

## Data quality analysis

- number of incomplete records;
- unavailable city-level data;
- inconsistent results;
- domains with multiple IPs.

---

# 16. Visualization Requirements

At minimum, generate:

1. Websites by country
2. Websites by organization/ISP
3. IPv4 vs IPv6
4. Successful vs failed lookups
5. Response-time distribution

Optional:

- geographic map;
- ASN distribution;
- city distribution;
- missing-data chart.

Charts must be generated from the actual 50-site dataset, not manually entered values.

---

# 17. Export Requirements

The application should support:

```text
CSV
```

as the primary research-data format.

Optional:

```text
Excel (.xlsx)
```

Exports should contain:

- column headers;
- timestamps;
- lookup status;
- all available result fields;
- field-test identifier.

Example:

```text
field_test_results.csv
```

---

# 18. Error Handling

The application must handle:

### Invalid input

```text
Please enter a valid domain or IP address.
```

### DNS failure

```text
Unable to resolve the domain.
```

### API timeout

```text
Geolocation service timed out.
```

### API rate limit

```text
Geolocation service rate limit reached.
```

### Missing geolocation

```text
Geolocation data is unavailable for this IP.
```

### Network unavailable

```text
Unable to connect to the geolocation service.
```

Errors must be understandable to a normal user.

Do not expose raw stack traces in the normal GUI.

Detailed technical information may be written to the log file.

---

# 19. Logging

Logging should capture important technical events:

```text
Application started
Lookup started
DNS resolution successful
DNS resolution failed
API request started
API response received
Database save successful
Export completed
Unexpected error
```

Logs should help debugging without storing unnecessary sensitive information.

---

# 20. Testing Strategy

Testing will happen throughout development.

## Unit tests

Test:

- domain validation;
- IP validation;
- normalization;
- analysis calculations.

## Integration tests

Test:

```text
Domain
  -> DNS
  -> API
  -> Normalizer
  -> Database
```

## GUI testing

Test:

- valid input;
- invalid input;
- empty input;
- API failure;
- DNS failure;
- loading state;
- result display;
- history;
- export.

## Field-test validation

Before running all 50 websites:

```text
Test 1 website
        |
        v
Verify result
        |
        v
Test 5 websites
        |
        v
Verify dataset
        |
        v
Run all 50
```

Do not run the entire experiment until the pipeline is stable.

---

# 21. Development Phases

## Phase 0 — Project Understanding & Requirements

Status: **Completed**

Define:

- objectives;
- scope;
- limitations;
- field-study purpose;
- architecture;
- expected deliverables.

---

## Phase 1 — Development Environment

Tasks:

- verify Python version;
- create project folder;
- create virtual environment;
- configure Antigravity 2.0 workspace;
- create Git repository if appropriate;
- create initial folder structure;
- create `requirements.txt`;
- create `.gitignore`;
- create `.env.example`;
- create initial README.

Deliverable:

```text
Clean project skeleton
```

Do not implement business logic yet.

---

## Phase 2 — Input Validation

Tasks:

- domain validation;
- IPv4 validation;
- IPv6 validation;
- input normalization;
- input type detection.

Deliverable:

```text
Reliable input-validation module
```

---

## Phase 3 — DNS Resolution

Tasks:

- domain-to-IP resolution;
- multiple-IP handling;
- IPv4/IPv6 distinction;
- DNS timing;
- DNS error handling.

Deliverable:

```text
Domain -> IP engine
```

Test with several known public domains.

---

## Phase 4 — Geolocation Service

Before implementation:

1. evaluate suitable providers;
2. choose one;
3. inspect its current free-tier/request limits;
4. inspect response fields;
5. create API configuration;
6. keep credentials outside source code.

Tasks:

- HTTP request;
- timeout;
- API errors;
- response parsing;
- normalized result.

Deliverable:

```text
IP -> geolocation engine
```

---

## Phase 5 — Integrated Lookup Engine

Combine:

```text
Validation
    +
DNS
    +
Geolocation
```

Deliverable:

```text
Domain/IP -> Complete structured result
```

At this point the core engine should work independently of the GUI.

---

## Phase 6 — Database & History

Tasks:

- SQLite setup;
- tables;
- insert;
- read;
- filtering;
- deletion;
- history retrieval.

Deliverable:

```text
Persistent lookup history
```

---

## Phase 7 — GUI

Tasks:

- main window;
- input section;
- analyze button;
- loading state;
- results table/cards;
- error messages;
- history view;
- professional styling.

Deliverable:

```text
Usable desktop application
```

---

## Phase 8 — Map Visualization

Tasks:

- latitude/longitude handling;
- map display;
- marker;
- approximate-location disclaimer;
- unavailable-coordinate handling.

Deliverable:

```text
Interactive/visual geographic result
```

---

## Phase 9 — Field-Test Module

Tasks:

- create 50-site input dataset;
- categorize websites;
- load CSV;
- process sites;
- record each result;
- show progress;
- preserve failures;
- prevent accidental duplicate records.

Deliverable:

```text
50-site testing system
```

---

## Phase 10 — Data Analysis

Tasks:

- clean dataset;
- validate records;
- calculate statistics;
- country distribution;
- ISP/organization distribution;
- ASN distribution;
- IPv4/IPv6;
- success/failure;
- response times;
- missing data.

Deliverable:

```text
Research-ready analysis
```

---

## Phase 11 — Charts & Dashboard Analytics

Tasks:

- generate charts;
- create summary cards;
- create analysis dashboard;
- use actual field-test data.

Deliverable:

```text
Analytics dashboard
```

---

## Phase 12 — Export

Tasks:

- CSV export;
- Excel export if required;
- analysis-summary export if useful;
- timestamped filenames.

Deliverable:

```text
Portable research dataset
```

---

## Phase 13 — Testing & Hardening

Tasks:

- unit testing;
- integration testing;
- GUI testing;
- error handling;
- API failure testing;
- offline/network failure testing;
- malformed input testing;
- database failure testing;
- export testing.

Deliverable:

```text
Stable application
```

---

## Phase 14 — Final Packaging

Tasks:

- clean source code;
- requirements;
- configuration template;
- README;
- screenshots;
- optional executable packaging;
- remove secrets;
- final test.

Deliverable:

```text
Submission-ready software
```

---

## Phase 15 — Field Project Report

The report should contain:

1. Title Page
2. Certificate/Declaration if required by college
3. Acknowledgement
4. Abstract
5. Introduction
6. Problem Statement
7. Objectives
8. Scope
9. Background/Technology
10. System Architecture
11. Methodology
12. Implementation
13. Field-Test Methodology
14. 50-Website Dataset
15. Results
16. Data Analysis
17. Charts
18. Limitations
19. Ethical Considerations
20. Conclusion
21. Future Scope
22. References

---

## Phase 16 — Viva Preparation

Prepare explanations for:

- What is an IP address?
- What is DNS?
- How does DNS resolution work?
- What is IPv4?
- What is IPv6?
- What is IP geolocation?
- How does an IP geolocation database work?
- Why is IP geolocation approximate?
- What is an ASN?
- What is an ISP/organization?
- Why can one domain have multiple IPs?
- What is a CDN?
- What happens when DNS fails?
- What happens when the API fails?
- Why store results in SQLite?
- Why use CSV?
- How were the 50 websites selected?
- What were the field-test limitations?
- What conclusions can and cannot be drawn?

---

# 22. Final Product Requirements

The final application should satisfy these requirements.

## Functional

- [ ] Domain lookup
- [ ] IP lookup
- [ ] IPv4 support
- [ ] IPv6 support where practical
- [ ] DNS resolution
- [ ] IP geolocation
- [ ] Network information
- [ ] Map visualization
- [ ] Lookup history
- [ ] 50-site field test
- [ ] Analytics
- [ ] Charts
- [ ] CSV export
- [ ] Optional Excel export

## Reliability

- [ ] Input validation
- [ ] DNS error handling
- [ ] API error handling
- [ ] Timeout handling
- [ ] Rate-limit handling
- [ ] Missing-data handling
- [ ] Logging
- [ ] Database error handling

## Research

- [ ] Fixed 50-site sample
- [ ] Test timestamp
- [ ] Reproducible methodology
- [ ] Raw/structured results
- [ ] Failed-result preservation
- [ ] Statistical analysis
- [ ] Limitations documented

## Documentation

- [ ] README
- [ ] Architecture document
- [ ] Installation instructions
- [ ] API configuration instructions
- [ ] User guide
- [ ] Field-test methodology
- [ ] Final report
- [ ] Viva preparation

---

# 23. Rules for Antigravity 2.0

Antigravity must follow these project rules.

### Rule 1 — Do not rewrite the whole project unnecessarily

Make targeted changes.

### Rule 2 — Do not change working functionality without a reason

Existing working features must remain functional.

### Rule 3 — Keep code readable

Prefer clear Python over unnecessary abstraction.

### Rule 4 — Explain important implementation decisions

When a major component is added, document what it does.

### Rule 5 — Do not hard-code secrets

API keys belong in environment configuration.

### Rule 6 — Do not fabricate data

Experimental results must come from actual lookups.

### Rule 7 — Preserve failed results

A failed lookup is still an experimental observation.

### Rule 8 — Do not claim exact geolocation

Use approximate IP geolocation terminology.

### Rule 9 — Test incrementally

Do not implement all phases at once.

### Rule 10 — Do not proceed to another phase automatically

Each phase must be completed and tested before the next phase begins.

### Rule 11 — Follow the current project requirements

If requirements change, update this architecture document before making major architectural changes.

### Rule 12 — Keep the project appropriate for a college field study

The project should be technically credible without unnecessary enterprise-level complexity.

---

# 24. Definition of Done

A phase is considered complete only when:

1. Its functionality is implemented.
2. The application starts successfully.
3. The relevant feature has been tested.
4. Expected and failure cases have been considered.
5. No known regression has been introduced.
6. The implementation is understandable.
7. The relevant documentation has been updated.
8. The user has reviewed/approved the phase.

Do not automatically continue to the next phase.

---

# 25. Final Architecture Goal

The finished project should represent this complete pipeline:

```text
                 USER
                  |
                  v
          +---------------+
          | Python GUI    |
          +-------+-------+
                  |
                  v
          +---------------+
          | Input         |
          | Validation    |
          +-------+-------+
                  |
          +-------+-------+
          |               |
       Domain             IP
          |               |
          v               |
      DNS Resolver        |
          |               |
          +-------+-------+
                  |
                  v
             IP Address
                  |
                  v
        +------------------+
        | Geolocation API  |
        +--------+---------+
                 |
                 v
        +------------------+
        | Normalize Result |
        +--------+---------+
                 |
       +---------+---------+
       |         |         |
       v         v         v
     GUI      SQLite     Analysis
       |                   |
       v                   v
     Map                 Charts
       |                   |
       +---------+---------+
                 |
                 v
             Export
                 |
                 v
       50-WEBSITE FIELD STUDY
                 |
                 v
       RESULTS + ANALYSIS
                 |
                 v
          FINAL REPORT
```

This document is the **master blueprint**, not a command to implement every phase immediately. Antigravity should implement only the phase explicitly authorized by the project workflow.
