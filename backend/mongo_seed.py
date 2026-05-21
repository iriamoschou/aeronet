"""
AeroNetB — MongoDB Seed Script
Creates QCReports, CertificationRecords, and IoTLogs collections
with sample documents that match the provided scenario JSON files.

Usage:
  python mongo_seed.py

Requires MONGO_URI in .env or as environment variable.
"""

import os, datetime
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://USER:PASS@cluster.mongodb.net/aeronetb")
MONGO_DB  = os.getenv("MONGO_DB",  "aeronetb")

client = MongoClient(MONGO_URI)
db     = client[MONGO_DB]

# ──────────────────────────────────────────────────────────────
# DROP EXISTING COLLECTIONS (clean seed)
# ──────────────────────────────────────────────────────────────
db.QCReports.drop()
db.CertificationRecords.drop()
db.IoTLogs.drop()
print("Dropped existing collections.")

# ──────────────────────────────────────────────────────────────
# QC REPORTS COLLECTION
# Mirrors Dim_NDT_report.json and EnvironmentalTest_report.json
# The nested result_payload varies by report type — key reason for
# document model (a fixed relational schema would require sparse tables)
# ──────────────────────────────────────────────────────────────
qc_reports = [
    # --- Dimensional + NDT report (mirrors Dim_NDT_report.json) ---
    {
        "report_id":            "QC-784512-A1",
        "delivered_item_id":    1,           # FK → PostgreSQL DeliveredItem.delivered_item_id
        "report_type":          "dimensional_NDT",
        "inspection_timestamp": "2025-08-28T10:00:00Z",
        "inspector_emp_id":     "EMP-002",
        "inspector_name":       "James Nakamura",
        "outcome_status":       "pass",
        "version_number":       1,
        "result_payload": {
            "visualInspection": "Pass",
            "dimensionalTolerance": {
                "result": "Pass",
                "measurements": [
                    {"dimension": "length", "measured": 15.002, "unit": "m"},
                    {"dimension": "width",  "measured":  3.499, "unit": "m"}
                ],
                "deviation": 0.002
            },
            "nondestructiveTesting": {
                "type":     "Ultrasonic",
                "result":   "Pass",
                "comments": "No internal defects detected."
            }
        },
        "tolerances": {"length_tolerance": 0.005, "width_tolerance": 0.003},
        "comments":   "All measurements within specification. Component approved.",
        "is_immutable": False
    },
    # --- Environmental stress test report (mirrors EnvironmentalTest_report.json) ---
    {
        "report_id":            "QC-889234-Z9",
        "delivered_item_id":    4,
        "report_type":          "environmental",
        "inspection_timestamp": "2025-09-01T14:30:00Z",
        "inspector_emp_id":     "EMP-002",
        "inspector_name":       "James Nakamura",
        "outcome_status":       "pass",
        "version_number":       1,
        "result_payload": {
            "environmentalTest": {
                "temperatureRange":   "-55 to 70C",
                "humidityExposure":   "95% RH for 48 hours",
                "result":             "Pass"
            },
            "notes": "Component withstood environmental stress without cracking or warping."
        },
        "tolerances":   {},
        "comments":     "Environmental test completed per AMS 2770 requirements.",
        "is_immutable": False
    },
    # --- Visual inspection report ---
    {
        "report_id":            "QC-901123-B3",
        "delivered_item_id":    2,
        "report_type":          "visual",
        "inspection_timestamp": "2025-12-08T09:00:00Z",
        "inspector_emp_id":     "EMP-002",
        "inspector_name":       "James Nakamura",
        "outcome_status":       "fail",
        "version_number":       1,
        "result_payload": {
            "surfaceCondition":   "Minor surface scuff on edge — 3 cm × 0.5 cm",
            "coatingIntegrity":   "Pass",
            "dimensionalCheck":   "Pass",
            "defectClassification": "Minor — cosmetic only"
        },
        "tolerances":   {},
        "comments":     "Surface scuff noted. Raised for disposition review. Production not impacted.",
        "is_immutable": False
    },
    # --- NDT report with fail outcome ---
    {
        "report_id":            "QC-920567-C4",
        "delivered_item_id":    3,
        "report_type":          "NDT",
        "inspection_timestamp": "2025-12-15T11:45:00Z",
        "inspector_emp_id":     "EMP-002",
        "inspector_name":       "James Nakamura",
        "outcome_status":       "fail",
        "version_number":       2,
        "result_payload": {
            "nondestructiveTesting": {
                "type":   "Radiographic",
                "result": "Fail",
                "defects_found": [
                    {"location": "rib_junction_A", "type": "micro_crack", "size_mm": 0.8}
                ],
                "comments": "Micro-crack detected at rib junction A. Part quarantined."
            }
        },
        "tolerances":   {"max_defect_size_mm": 0.5},
        "comments":     "Part rejected. Returned to SkyStar Parts Ltd for replacement.",
        "is_immutable": False
    }
]

db.QCReports.insert_many(qc_reports)
db.QCReports.create_index([("delivered_item_id", ASCENDING)])
db.QCReports.create_index([("inspector_emp_id",  ASCENDING)])
db.QCReports.create_index([("outcome_status",    ASCENDING)])
print(f"Inserted {len(qc_reports)} QC reports.")

# ──────────────────────────────────────────────────────────────
# CERTIFICATION RECORDS COLLECTION
# Immutable once approved — approval_status=approved sets is_immutable=True
# Document model used because evidence composition varies by certification context
# ──────────────────────────────────────────────────────────────
cert_records = [
    {
        "cert_id":                  "CERT-2025-001",
        "delivered_item_id":        1,
        "certification_type":       "Component_Airworthiness",
        "approval_status":          "approved",
        "approval_date":            "2025-11-14T16:00:00Z",
        "inspector_details": {
            "emp_id": "EMP-002",
            "name":   "James Nakamura",
            "cert_ids": ["NDT-cert-GB-2021", "DIM-cert-GB-2022"]
        },
        "digital_signature_ref":        "SIG-JN-002-20251114",
        "material_traceability_ref":    "BATCH-AC-2025-OCT-07 → Raw Al7075-T6 Cert MC-7075-2025-09",
        "certification_notes":          "Component meets AS9100 and EASA Part 21 requirements. Released to service.",
        "supporting_evidence_refs": [
            "/storage/certs/CERT-2025-001-qc-report.pdf",
            "/storage/certs/CERT-2025-001-material-cert.pdf"
        ],
        "is_immutable": True,   # Approved certifications are locked — no further edits
        "created_at":   "2025-11-13T08:00:00Z"
    },
    {
        "cert_id":                  "CERT-2025-002",
        "delivered_item_id":        4,
        "certification_type":       "Material_Traceability",
        "approval_status":          "approved",
        "approval_date":            "2025-12-10T14:30:00Z",
        "inspector_details": {
            "emp_id": "EMP-002",
            "name":   "James Nakamura",
            "cert_ids": ["NDT-cert-GB-2021"]
        },
        "digital_signature_ref":        "SIG-JN-002-20251210",
        "material_traceability_ref":    "BATCH-SS-2025-NOV-06 → Raw Al7075 Cert MC-7075-2025-11",
        "certification_notes":          "Material batch verified. Traceability confirmed to raw material origin.",
        "supporting_evidence_refs": [
            "/storage/certs/CERT-2025-002-material-batch.pdf"
        ],
        "is_immutable": True,
        "created_at":   "2025-12-09T09:00:00Z"
    },
    {
        "cert_id":                  "CERT-2026-001",
        "delivered_item_id":        5,
        "certification_type":       "Component_Airworthiness",
        "approval_status":          "draft",
        "approval_date":            None,
        "inspector_details": {
            "emp_id": "EMP-002",
            "name":   "James Nakamura",
            "cert_ids": ["NDT-cert-GB-2021", "DIM-cert-GB-2022"]
        },
        "digital_signature_ref":        "",
        "material_traceability_ref":    "BATCH-SS-2025-NOV-06",
        "certification_notes":          "Pending final dimensional check before approval.",
        "supporting_evidence_refs": [],
        "is_immutable": False,
        "created_at":   "2026-01-08T10:00:00Z"
    }
]

db.CertificationRecords.insert_many(cert_records)
db.CertificationRecords.create_index([("delivered_item_id",  ASCENDING)])
db.CertificationRecords.create_index([("certification_type", ASCENDING)])
db.CertificationRecords.create_index([("approval_status",    ASCENDING)])
print(f"Inserted {len(cert_records)} certification records.")

# ──────────────────────────────────────────────────────────────
# IoT LOGS COLLECTION
# Mirrors MEQuip_IoT.json sensor structure
# Document model because different devices emit different reading schemas
# readings object varies by sensor type — document avoids sparse relational columns
# ──────────────────────────────────────────────────────────────
def make_log(device_id, context_id, temp, vib, pressure, gps, alert):
    return {
        "iot_device_id": device_id,    # FK → PostgreSQL IoTDevice.device_identifier
        "context_id":    context_id,
        "timestamp":     datetime.datetime.utcnow().isoformat(),
        "readings": {
            "temperature": temp,
            "vibration":   vib,
            "pressure":    pressure,
            "gps_location": gps
        },
        "alert_flag": alert
    }

iot_logs = [
    # CNC Mill Alpha-7 — normal operation
    make_log("IOT-CNC-A7-T01", "EQUIP-001", 72.4, 0.12, None, None, False),
    make_log("IOT-CNC-A7-T01", "EQUIP-001", 74.1, 0.14, None, None, False),
    make_log("IOT-CNC-A7-V01", "EQUIP-001", None, 0.31, None, None, False),
    # CNC Mill Alpha-7 — vibration alert
    make_log("IOT-CNC-A7-V01", "EQUIP-001", None, 1.87, None, None, True),
    # Autoclave — normal
    make_log("IOT-AC-B2-T01",  "EQUIP-002", 182.3, None, 3.4, None, False),
    make_log("IOT-AC-B2-T01",  "EQUIP-002", 183.0, None, 3.5, None, False),
    # Transit container — with GPS, temperature alert (cold chain breach)
    {
        "iot_device_id": "IOT-TC9-GPS-01",
        "context_id":    "SHIPMENT-TRK-20260108-003",
        "timestamp":     datetime.datetime.utcnow().isoformat(),
        "readings": {
            "temperature":  -8.5,   # below limit — cold chain breach alert
            "vibration":     0.05,
            "pressure":      None,
            "gps_location": {"lat": 52.3676, "lon": 4.9041, "description": "Rotterdam Port Area"}
        },
        "alert_flag": True   # temperature below -5C threshold
    },
    {
        "iot_device_id": "IOT-TC9-GPS-01",
        "context_id":    "SHIPMENT-TRK-20260108-003",
        "timestamp":     datetime.datetime.utcnow().isoformat(),
        "readings": {
            "temperature":  4.2,
            "vibration":    0.03,
            "pressure":     None,
            "gps_location": {"lat": 52.3676, "lon": 4.9041, "description": "Rotterdam Port Area"}
        },
        "alert_flag": False
    },
    # Heat Treatment Furnace — high temperature alert
    make_log("IOT-HTF-T01", "EQUIP-004", 1250.0, None, None, None, True),
    make_log("IOT-HTF-T01", "EQUIP-004",  985.0, None, None, None, False),
    # NDT Station — normal
    make_log("IOT-NDT-S01", "EQUIP-005", None, 0.04, None, None, False),
]

db.IoTLogs.insert_many(iot_logs)
db.IoTLogs.create_index([("iot_device_id", ASCENDING)])
db.IoTLogs.create_index([("alert_flag",    ASCENDING)])
db.IoTLogs.create_index([("timestamp",     ASCENDING)])
print(f"Inserted {len(iot_logs)} IoT log entries.")

client.close()
print("\n✅ MongoDB seed complete. Collections: QCReports, CertificationRecords, IoTLogs")
print("   Indexes created on key query fields.")
