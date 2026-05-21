# AeroNetB Aerospace Supply Chain Management System
**Student ID: 100774688 | Module: 5CM506 Data Driven Systems | University of Derby**

---

## System Overview

A full-stack hybrid database application for AeroNetB Aerospace. The system uses:
- **PostgreSQL** — structured relational data (suppliers, orders, shipments, RBAC, audit logs)
- **MongoDB Atlas** — semi-structured document data (QC reports, certifications, IoT logs)
- **Python Flask** — REST API backend with JWT authentication and RBAC
- **HTML/Bootstrap/Chart.js** — role-aware dashboard frontend (served by Flask)

---

## Prerequisites

Install these before starting:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ | https://python.org |
| PostgreSQL | 14+ | https://postgresql.org/download |
| Git | Any | https://git-scm.com |

MongoDB runs on **Atlas free tier** — no local installation needed.

---

## Setup Instructions (do these in order)

### Step 1 — PostgreSQL: create the database

Open psql or pgAdmin and run:
```sql
CREATE DATABASE aeronetb;
```

Then run the DDL and DML scripts:
```bash
psql -U postgres -d aeronetb -f scripts/ddl.sql
psql -U postgres -d aeronetb -f scripts/dml.sql
```

### Step 2 — MongoDB Atlas: create free cluster

1. Go to https://cloud.mongodb.com and sign up (free)
2. Create a free M0 cluster (any region)
3. Create a database user under **Security → Database Access**
4. Allow your IP under **Security → Network Access** (or allow all: 0.0.0.0/0 for demo)
5. Click **Connect → Drivers** and copy your connection string (looks like `mongodb+srv://...`)

### Step 3 — Configure environment variables

```bash
cd backend
cp .env.template .env
```

Edit `.env` and fill in:
- Your PostgreSQL password
- Your MongoDB Atlas connection string

### Step 4 — Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 5 — Seed MongoDB

```bash
cd backend
python mongo_seed.py
```

You should see:
```
Inserted 4 QC reports.
Inserted 3 certification records.
Inserted 11 IoT log entries.
✅ MongoDB seed complete.
```

### Step 6 — Set demo user passwords

```bash
cd backend
python setup_passwords.py
```

### Step 7 — Run the Flask server

```bash
cd backend
python app.py
```

Open your browser at: **http://localhost:5000**

---

## Demo Login Accounts

| Email | Password | Role |
|-------|----------|------|
| sarah.mitchell@aeronetb.com | Demo1234! | Procurement Officer |
| james.nakamura@aeronetb.com | Demo1234! | Quality Inspector |
| fatima.alrashid@aeronetb.com | Demo1234! | Supply Chain Manager |
| david.okafor@aeronetb.com | Demo1234! | Equipment Engineer |
| elena.vasquez@regulator.eu | Demo1234! | Auditor (read-only) |

---

## API Endpoints Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/auth/login | User login, returns JWT token | None |
| GET | /api/auth/me | Current user info | Token |
| GET | /api/suppliers | List all suppliers | Token |
| POST | /api/suppliers | Create supplier | ProcurementOfficer |
| GET | /api/suppliers/\<id\> | Get supplier detail | Token |
| GET | /api/parts | List all parts with specs | Token |
| GET | /api/orders | List all purchase orders | Token |
| POST | /api/orders | Create purchase order | ProcurementOfficer |
| GET | /api/orders/\<id\> | Order detail with lines | Token |
| GET | /api/shipments | List shipments | Token |
| GET | /api/shipments/\<id\>/events | Shipment event history | Token |
| GET | /api/delivered-items | Delivered item traceability | Token |
| GET | /api/qc/reports | List QC reports (MongoDB) | Token |
| POST | /api/qc/reports | Create QC report (MongoDB) | QualityInspector |
| GET | /api/qc/reports/\<id\> | Single QC report | Token |
| GET | /api/certifications | List certifications (MongoDB) | Token |
| POST | /api/certifications | Create certification (MongoDB) | QualityInspector |
| POST | /api/certifications/\<id\>/approve | Approve & lock cert (immutable) | QualityInspector |
| GET | /api/iot/logs | IoT sensor logs (MongoDB) | Token |
| GET | /api/iot/devices | IoT devices (PostgreSQL) | Token |
| GET | /api/equipment | Equipment list | Token |
| GET | /api/dashboard/supplier-kpis | Supplier on-time delivery analytics | Token |
| GET | /api/dashboard/shipment-overview | Shipment status breakdown + delayed | Token |
| GET | /api/dashboard/qc-summary | QC pass/fail summary | Token |
| GET | /api/dashboard/iot-alerts | Equipment issues + IoT alerts | Token |
| GET | /api/audit-logs | Full audit trail | Auditor, SupplyChainManager |
| GET | /api/health | System health check | None |

---

## Project Structure

```
aeronetb/
├── scripts/
│   ├── ddl.sql            — PostgreSQL schema (all tables, constraints, indexes)
│   └── dml.sql            — Dummy data (suppliers, parts, orders, users, equipment)
├── backend/
│   ├── app.py             — Flask API (all routes, RBAC, audit logging)
│   ├── mongo_seed.py      — MongoDB collection setup and seed data
│   ├── setup_passwords.py — Sets real password hashes for demo accounts
│   ├── requirements.txt   — Python dependencies
│   └── .env.template      — Environment variable template
├── frontend/
│   └── index.html         — Complete dashboard (login + role views + charts)
└── README.md
```

---

## Security Features Implemented

- **JWT authentication** — tokens expire after 8 hours
- **Role-Based Access Control (RBAC)** — enforced at every API endpoint via decorators
- **Immutable certifications** — once approved, certification records cannot be edited
- **Audit logging** — every login, data access, and modification is recorded with user ID, IP, timestamp, and outcome
- **Password hashing** — all passwords stored as PBKDF2-SHA256 hashes (werkzeug)
- **Auditor read-only enforcement** — Auditor role blocked from write operations at API and UI level

---

## Deployment (Local — for demo)

The system runs entirely locally:
- Flask serves both the API (`/api/*`) and the frontend (`/`)
- PostgreSQL runs locally on port 5432
- MongoDB runs on Atlas (free cloud tier)

No additional web server (nginx, Apache) is required for the demo.
