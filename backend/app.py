"""
AeroNetB Aerospace Supply Chain Management System
Backend API — Flask + PostgreSQL + MongoDB
Student ID: 100774688 | Module: 5CM506 Data Driven Systems

Routes:
  POST   /api/auth/login
  GET    /api/auth/me

  GET    /api/suppliers
  POST   /api/suppliers
  GET    /api/suppliers/<id>

  GET    /api/parts

  GET    /api/orders
  POST   /api/orders
  GET    /api/orders/<id>

  GET    /api/shipments
  GET    /api/shipments/<id>/events

  GET    /api/delivered-items

  GET    /api/qc/reports            (MongoDB)
  POST   /api/qc/reports            (MongoDB)
  GET    /api/qc/reports/<id>       (MongoDB)

  GET    /api/certifications        (MongoDB)
  POST   /api/certifications        (MongoDB, approve = immutable)

  GET    /api/iot/logs              (MongoDB)
  GET    /api/iot/devices

  GET    /api/equipment

  GET    /api/dashboard/supplier-kpis
  GET    /api/dashboard/shipment-overview
  GET    /api/dashboard/qc-summary
  GET    /api/dashboard/iot-alerts

  GET    /api/audit-logs
"""

import os, datetime, traceback
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps as bson_dumps
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────
# APP SETUP
# ──────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app, resources={r"/api/*": {"origins": "*"}})

SECRET_KEY  = os.getenv("SECRET_KEY",   "aeronetb-dev-secret-2026-change-in-prod")
PG_DSN      = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/aeronetb")
MONGO_URI   = os.getenv("MONGO_URI",    "mongodb+srv://USER:PASS@cluster.mongodb.net/aeronetb")
MONGO_DB    = os.getenv("MONGO_DB",     "aeronetb")

# MongoDB client (initialised once)
_mongo_client = None

def get_mongo():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _mongo_client[MONGO_DB]

def get_pg():
    """Return a new PostgreSQL connection with RealDictCursor."""
    return psycopg2.connect(PG_DSN, cursor_factory=psycopg2.extras.RealDictCursor)

# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────
def _json_serial(obj):
    """JSON serialiser for datetime objects returned by psycopg2."""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serialisable")

def pg_query(sql, params=None, fetch="all"):
    conn = get_pg()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetch == "all":
                return [dict(r) for r in cur.fetchall()]
            if fetch == "one":
                row = cur.fetchone()
                return dict(row) if row else None
            return None
    finally:
        conn.close()

def pg_execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE and return last inserted id if any."""
    conn = get_pg()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            try:
                return cur.fetchone()[0]
            except Exception:
                return None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def _bson_to_dict(doc):
    """Convert MongoDB document to JSON-safe dict."""
    if doc is None:
        return None
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    return doc

def audit(user_id, action, entity_type=None, entity_id=None, desc=None, outcome="success"):
    """Write a row to AuditLog asynchronously (best-effort)."""
    try:
        ip = request.remote_addr
        pg_execute(
            """INSERT INTO AuditLog
               (user_id, action_type, entity_type, entity_id, description, ip_address, outcome)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (user_id, action, entity_type, entity_id, desc, ip, outcome)
        )
    except Exception as e:
        print(f"[audit error] {e}")

# ──────────────────────────────────────────────────────────────
# AUTH DECORATORS
# ──────────────────────────────────────────────────────────────
def decode_token():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    if not token:
        return None, "Token missing"
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"]), None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payload, err = decode_token()
        if err:
            return jsonify({"error": err}), 401
        request.user = payload
        return f(*args, **kwargs)
    return decorated

def role_required(*allowed_roles):
    """Decorator: user must hold one of the listed roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            payload, err = decode_token()
            if err:
                return jsonify({"error": err}), 401
            if payload.get("role") not in allowed_roles:
                audit(payload.get("user_id"), "ACCESS_DENIED", desc=f"Attempted {request.path}", outcome="failure")
                return jsonify({"error": "Access denied for your role"}), 403
            request.user = payload
            return f(*args, **kwargs)
        return decorated
    return decorator

# ──────────────────────────────────────────────────────────────
# FRONTEND SERVING (Flask serves the HTML files directly)
# ──────────────────────────────────────────────────────────────
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    try:
        return send_from_directory(app.static_folder, path)
    except Exception:
        return send_from_directory(app.static_folder, "index.html")

# ──────────────────────────────────────────────────────────────
# AUTH ROUTES
# ──────────────────────────────────────────────────────────────
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = pg_query(
        """SELECT u.user_id, u.emp_id, u.full_name, u.email,
                  u.password_hash, u.is_active, u.department,
                  r.role_name
           FROM   SystemUser u
           LEFT JOIN UserRole  ur ON u.user_id = ur.user_id
           LEFT JOIN Role      r  ON ur.role_id = r.role_id
           WHERE  u.email = %s""",
        (email,), fetch="one"
    )

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not check_password_hash(user["password_hash"], password):
        audit(user["user_id"], "LOGIN_FAILED", desc=f"Bad password for {email}", outcome="failure")
        return jsonify({"error": "Invalid credentials"}), 401

    if not user["is_active"]:
        return jsonify({"error": "Account is disabled"}), 403

    token = jwt.encode({
        "user_id":   user["user_id"],
        "emp_id":    user["emp_id"],
        "full_name": user["full_name"],
        "role":      user["role_name"],
        "exp":       datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }, SECRET_KEY, algorithm="HS256")

    audit(user["user_id"], "LOGIN", "SystemUser", user["user_id"], f"{email} logged in")

    return jsonify({
        "token": token,
        "user": {
            "user_id":   user["user_id"],
            "full_name": user["full_name"],
            "role":      user["role_name"],
            "emp_id":    user["emp_id"],
            "department":user["department"]
        }
    })

@app.route("/api/auth/me", methods=["GET"])
@token_required
def me():
    return jsonify(request.user)

# ──────────────────────────────────────────────────────────────
# SUPPLIERS
# ──────────────────────────────────────────────────────────────
@app.route("/api/suppliers", methods=["GET"])
@token_required
def get_suppliers():
    suppliers = pg_query("SELECT * FROM Supplier ORDER BY business_name")
    audit(request.user["user_id"], "VIEW", "Supplier", desc="Listed all suppliers")
    return jsonify(suppliers)

@app.route("/api/suppliers/<int:sid>", methods=["GET"])
@token_required
def get_supplier(sid):
    supplier = pg_query("SELECT * FROM Supplier WHERE supplier_id=%s", (sid,), fetch="one")
    if not supplier:
        return jsonify({"error": "Supplier not found"}), 404
    audit(request.user["user_id"], "VIEW", "Supplier", sid)
    return jsonify(supplier)

@app.route("/api/suppliers", methods=["POST"])
@role_required("ProcurementOfficer")
def create_supplier():
    d = request.get_json() or {}
    required = ["business_name"]
    if not all(d.get(k) for k in required):
        return jsonify({"error": "business_name is required"}), 400
    new_id = pg_execute(
        """INSERT INTO Supplier (business_name,address,country,accreditation_status,contact_email,contact_phone)
           VALUES (%s,%s,%s,%s,%s,%s) RETURNING supplier_id""",
        (d.get("business_name"), d.get("address"), d.get("country"),
         d.get("accreditation_status"), d.get("contact_email"), d.get("contact_phone"))
    )
    audit(request.user["user_id"], "CREATE", "Supplier", new_id, f"Created supplier {d['business_name']}")
    return jsonify({"supplier_id": new_id, "message": "Supplier created"}), 201

# ──────────────────────────────────────────────────────────────
# PARTS
# ──────────────────────────────────────────────────────────────
@app.route("/api/parts", methods=["GET"])
@token_required
def get_parts():
    parts = pg_query(
        """SELECT p.*, pbs.tensile_strength_mpa, pbs.fatigue_limit_mpa, pbs.process_details
           FROM Part p
           LEFT JOIN PartBaselineSpecification pbs ON p.part_id = pbs.part_id
           ORDER BY p.part_code"""
    )
    return jsonify(parts)

# ──────────────────────────────────────────────────────────────
# PURCHASE ORDERS
# ──────────────────────────────────────────────────────────────
@app.route("/api/orders", methods=["GET"])
@token_required
def get_orders():
    orders = pg_query(
        """SELECT po.*, s.business_name AS supplier_name,
                  u.full_name AS created_by_name
           FROM PurchaseOrder po
           JOIN Supplier s    ON po.supplier_id = s.supplier_id
           LEFT JOIN SystemUser u ON po.created_by = u.user_id
           ORDER BY po.order_date DESC"""
    )
    audit(request.user["user_id"], "VIEW", "PurchaseOrder", desc="Listed all orders")
    return jsonify(orders)

@app.route("/api/orders/<int:oid>", methods=["GET"])
@token_required
def get_order(oid):
    order = pg_query(
        """SELECT po.*, s.business_name AS supplier_name
           FROM PurchaseOrder po JOIN Supplier s ON po.supplier_id=s.supplier_id
           WHERE po.order_id=%s""",
        (oid,), fetch="one"
    )
    if not order:
        return jsonify({"error": "Order not found"}), 404

    lines = pg_query(
        """SELECT pol.*, spo.supplier_part_code, p.part_name
           FROM PurchaseOrderLine pol
           JOIN SupplierPartOffering spo ON pol.offering_id = spo.offering_id
           JOIN Part p ON spo.part_id = p.part_id
           WHERE pol.order_id = %s""",
        (oid,)
    )
    order["lines"] = lines
    audit(request.user["user_id"], "VIEW", "PurchaseOrder", oid)
    return jsonify(order)

@app.route("/api/orders", methods=["POST"])
@role_required("ProcurementOfficer")
def create_order():
    d = request.get_json() or {}
    if not d.get("supplier_id") or not d.get("order_date"):
        return jsonify({"error": "supplier_id and order_date required"}), 400
    new_id = pg_execute(
        """INSERT INTO PurchaseOrder
           (supplier_id, created_by, order_date, desired_delivery_date, status, total_value, notes)
           VALUES (%s,%s,%s,%s,'placed',%s,%s) RETURNING order_id""",
        (d["supplier_id"], request.user["user_id"], d["order_date"],
         d.get("desired_delivery_date"), d.get("total_value"), d.get("notes"))
    )
    audit(request.user["user_id"], "CREATE", "PurchaseOrder", new_id, f"Created order for supplier {d['supplier_id']}")
    return jsonify({"order_id": new_id, "message": "Order created"}), 201

# ──────────────────────────────────────────────────────────────
# SHIPMENTS
# ──────────────────────────────────────────────────────────────
@app.route("/api/shipments", methods=["GET"])
@token_required
def get_shipments():
    shipments = pg_query(
        """SELECT sh.*, po.order_date, s.business_name AS supplier_name
           FROM Shipment sh
           JOIN PurchaseOrder po ON sh.order_id = po.order_id
           JOIN Supplier s ON po.supplier_id = s.supplier_id
           ORDER BY sh.created_at DESC"""
    )
    return jsonify(shipments)

@app.route("/api/shipments/<int:sid>/events", methods=["GET"])
@token_required
def get_shipment_events(sid):
    events = pg_query(
        "SELECT * FROM ShipmentEvent WHERE shipment_id=%s ORDER BY event_timestamp",
        (sid,)
    )
    return jsonify(events)

# ──────────────────────────────────────────────────────────────
# DELIVERED ITEMS
# ──────────────────────────────────────────────────────────────
@app.route("/api/delivered-items", methods=["GET"])
@token_required
def get_delivered_items():
    items = pg_query(
        """SELECT di.*, p.part_name, p.part_code, s.business_name AS supplier_name
           FROM DeliveredItem di
           JOIN PurchaseOrderLine pol ON di.line_id = pol.line_id
           JOIN SupplierPartOffering spo ON pol.offering_id = spo.offering_id
           JOIN Part p ON spo.part_id = p.part_id
           JOIN Supplier s ON spo.supplier_id = s.supplier_id
           ORDER BY di.delivery_timestamp DESC"""
    )
    return jsonify(items)

# ──────────────────────────────────────────────────────────────
# QC REPORTS (MongoDB)
# ──────────────────────────────────────────────────────────────
@app.route("/api/qc/reports", methods=["GET"])
@token_required
def get_qc_reports():
    db = get_mongo()
    docs = list(db.QCReports.find().sort("inspection_timestamp", -1).limit(100))
    result = [_bson_to_dict(d) for d in docs]
    audit(request.user["user_id"], "VIEW", "QCReport", desc="Listed QC reports")
    return jsonify(result)

@app.route("/api/qc/reports/<report_id>", methods=["GET"])
@token_required
def get_qc_report(report_id):
    db = get_mongo()
    try:
        doc = db.QCReports.find_one({"_id": ObjectId(report_id)})
    except Exception:
        doc = db.QCReports.find_one({"report_id": report_id})
    if not doc:
        return jsonify({"error": "Report not found"}), 404
    return jsonify(_bson_to_dict(doc))

@app.route("/api/qc/reports", methods=["POST"])
@role_required("QualityInspector")
def create_qc_report():
    d = request.get_json() or {}
    if not d.get("delivered_item_id") or not d.get("report_type"):
        return jsonify({"error": "delivered_item_id and report_type required"}), 400

    db = get_mongo()
    doc = {
        "report_id":            d.get("report_id", f"QC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"),
        "delivered_item_id":    d["delivered_item_id"],
        "report_type":          d["report_type"],          # dimensional, NDT, environmental, visual
        "inspection_timestamp": datetime.datetime.utcnow().isoformat(),
        "inspector_emp_id":     request.user["emp_id"],
        "inspector_name":       request.user["full_name"],
        "outcome_status":       d.get("outcome_status", "pending"),
        "version_number":       1,
        "result_payload":       d.get("result_payload", {}),
        "measurement_values":   d.get("measurement_values", []),
        "tolerances":           d.get("tolerances", {}),
        "comments":             d.get("comments", ""),
        "is_immutable":         False
    }
    result = db.QCReports.insert_one(doc)
    audit(request.user["user_id"], "CREATE", "QCReport", desc=f"Created report {doc['report_id']}")
    return jsonify({"id": str(result.inserted_id), "report_id": doc["report_id"]}), 201

# ──────────────────────────────────────────────────────────────
# CERTIFICATIONS (MongoDB — immutable once approved)
# ──────────────────────────────────────────────────────────────
@app.route("/api/certifications", methods=["GET"])
@token_required
def get_certifications():
    db = get_mongo()
    # Auditors and SupplyChainManagers see all; Inspectors see their own
    role = request.user.get("role")
    query = {} if role in ("Auditor", "SupplyChainManager", "ProcurementOfficer") else \
            {"inspector_emp_id": request.user["emp_id"]}
    docs = list(db.CertificationRecords.find(query).sort("approval_date", -1).limit(100))
    audit(request.user["user_id"], "VIEW", "CertificationRecord", desc="Listed certifications")
    return jsonify([_bson_to_dict(d) for d in docs])

@app.route("/api/certifications", methods=["POST"])
@role_required("QualityInspector")
def create_certification():
    d = request.get_json() or {}
    if not d.get("delivered_item_id") or not d.get("certification_type"):
        return jsonify({"error": "delivered_item_id and certification_type required"}), 400

    db = get_mongo()
    doc = {
        "cert_id":                  d.get("cert_id", f"CERT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"),
        "delivered_item_id":        d["delivered_item_id"],
        "certification_type":       d["certification_type"],
        "approval_status":          "draft",
        "approval_date":            None,
        "inspector_details":        {
            "emp_id": request.user["emp_id"],
            "name":   request.user["full_name"]
        },
        "digital_signature_ref":    d.get("digital_signature_ref", ""),
        "material_traceability_ref":d.get("material_traceability_ref", ""),
        "certification_notes":      d.get("certification_notes", ""),
        "is_immutable":             False,   # becomes True on approve
        "created_at":               datetime.datetime.utcnow().isoformat()
    }
    result = db.CertificationRecords.insert_one(doc)
    audit(request.user["user_id"], "CREATE", "CertificationRecord", desc=f"Created cert {doc['cert_id']}")
    return jsonify({"id": str(result.inserted_id), "cert_id": doc["cert_id"]}), 201

@app.route("/api/certifications/<cert_id>/approve", methods=["POST"])
@role_required("QualityInspector")
def approve_certification(cert_id):
    """Once approved, certification is set immutable — no further edits permitted."""
    db = get_mongo()
    doc = db.CertificationRecords.find_one({"cert_id": cert_id})
    if not doc:
        return jsonify({"error": "Certification not found"}), 404
    if doc.get("is_immutable"):
        return jsonify({"error": "Certification is already approved and immutable"}), 409

    db.CertificationRecords.update_one(
        {"cert_id": cert_id},
        {"$set": {
            "approval_status": "approved",
            "approval_date":   datetime.datetime.utcnow().isoformat(),
            "is_immutable":    True
        }}
    )
    audit(request.user["user_id"], "APPROVE", "CertificationRecord", desc=f"Approved cert {cert_id}")
    return jsonify({"message": "Certification approved and locked as immutable"})

# ──────────────────────────────────────────────────────────────
# IoT LOGS (MongoDB)
# ──────────────────────────────────────────────────────────────
@app.route("/api/iot/logs", methods=["GET"])
@token_required
def get_iot_logs():
    db = get_mongo()
    device_id = request.args.get("device_id")
    query = {"iot_device_id": device_id} if device_id else {}
    docs = list(db.IoTLogs.find(query).sort("timestamp", -1).limit(200))
    return jsonify([_bson_to_dict(d) for d in docs])

@app.route("/api/iot/devices", methods=["GET"])
@token_required
def get_iot_devices():
    devices = pg_query(
        """SELECT d.*, e.equipment_name, e.facility, e.status AS equipment_status
           FROM IoTDevice d JOIN Equipment e ON d.equipment_id = e.equipment_id
           ORDER BY e.equipment_name"""
    )
    return jsonify(devices)

@app.route("/api/equipment", methods=["GET"])
@token_required
def get_equipment():
    equip = pg_query("SELECT * FROM Equipment ORDER BY equipment_name")
    return jsonify(equip)

# ──────────────────────────────────────────────────────────────
# DASHBOARD ANALYTICS
# ──────────────────────────────────────────────────────────────
@app.route("/api/dashboard/supplier-kpis", methods=["GET"])
@token_required
def supplier_kpis():
    """On-time delivery rate and order count per supplier."""
    data = pg_query(
        """SELECT s.supplier_id, s.business_name,
                  COUNT(po.order_id)                                       AS total_orders,
                  SUM(CASE WHEN po.status='completed' THEN 1 ELSE 0 END)  AS completed_orders,
                  SUM(CASE WHEN po.actual_delivery_date <= po.desired_delivery_date
                           AND po.status='completed' THEN 1 ELSE 0 END)    AS on_time_orders,
                  ROUND(
                    100.0 * SUM(CASE WHEN po.actual_delivery_date <= po.desired_delivery_date
                                     AND po.status='completed' THEN 1 ELSE 0 END)
                    / NULLIF(SUM(CASE WHEN po.status='completed' THEN 1 ELSE 0 END),0)
                  ,1)                                                       AS on_time_pct
           FROM Supplier s
           LEFT JOIN PurchaseOrder po ON s.supplier_id = po.supplier_id
           GROUP BY s.supplier_id, s.business_name
           ORDER BY on_time_pct DESC NULLS LAST"""
    )
    return jsonify(data)

@app.route("/api/dashboard/shipment-overview", methods=["GET"])
@token_required
def shipment_overview():
    """Count of shipments by status, plus delayed shipments list."""
    by_status = pg_query(
        """SELECT status, COUNT(*) AS count
           FROM Shipment GROUP BY status ORDER BY count DESC"""
    )
    delayed = pg_query(
        """SELECT sh.shipment_id, sh.tracking_number, sh.eta_date, sh.status,
                  s.business_name AS supplier_name
           FROM Shipment sh
           JOIN PurchaseOrder po ON sh.order_id = po.order_id
           JOIN Supplier s ON po.supplier_id = s.supplier_id
           WHERE sh.eta_date < CURRENT_DATE AND sh.status NOT IN ('delivered')
           ORDER BY sh.eta_date"""
    )
    return jsonify({"by_status": by_status, "delayed": delayed})

@app.route("/api/dashboard/qc-summary", methods=["GET"])
@token_required
def qc_summary():
    """QC pass/fail breakdown from MongoDB."""
    db = get_mongo()
    pipeline = [
        {"$group": {
            "_id": "$outcome_status",
            "count": {"$sum": 1}
        }}
    ]
    by_outcome = list(db.QCReports.aggregate(pipeline))
    for doc in by_outcome:
        doc["outcome_status"] = doc.pop("_id")

    by_type = list(db.QCReports.aggregate([
        {"$group": {"_id": "$report_type", "count": {"$sum": 1}}}
    ]))
    for doc in by_type:
        doc["report_type"] = doc.pop("_id")

    return jsonify({"by_outcome": by_outcome, "by_type": by_type})

@app.route("/api/dashboard/iot-alerts", methods=["GET"])
@token_required
def iot_alerts():
    """Equipment with non-operational status, plus latest alert flags from MongoDB."""
    equipment = pg_query(
        "SELECT * FROM Equipment WHERE status != 'operational' ORDER BY status"
    )
    db = get_mongo()
    alerts = list(db.IoTLogs.find({"alert_flag": True}).sort("timestamp", -1).limit(20))
    return jsonify({"equipment_issues": equipment, "iot_alerts": [_bson_to_dict(a) for a in alerts]})

# ──────────────────────────────────────────────────────────────
# AUDIT LOGS (Auditor only)
# ──────────────────────────────────────────────────────────────
@app.route("/api/audit-logs", methods=["GET"])
@role_required("Auditor", "SupplyChainManager")
def get_audit_logs():
    logs = pg_query(
        """SELECT al.*, u.full_name, u.emp_id
           FROM AuditLog al
           LEFT JOIN SystemUser u ON al.user_id = u.user_id
           ORDER BY al.created_at DESC LIMIT 500"""
    )
    return jsonify(logs)

# ──────────────────────────────────────────────────────────────
# HEALTH CHECK
# ──────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    pg_ok, mongo_ok = False, False
    try:
        pg_query("SELECT 1", fetch="one")
        pg_ok = True
    except Exception:
        pass
    try:
        get_mongo().command("ping")
        mongo_ok = True
    except Exception:
        pass
    return jsonify({
        "status": "ok" if (pg_ok and mongo_ok) else "degraded",
        "postgresql": "connected" if pg_ok else "error",
        "mongodb":    "connected" if mongo_ok else "error",
        "timestamp":  datetime.datetime.utcnow().isoformat()
    })

# ──────────────────────────────────────────────────────────────
# ERROR HANDLERS
# ──────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    traceback.print_exc()
    return jsonify({"error": "Internal server error"}), 500

# ──────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"[AeroNetB API] Running on http://localhost:{port}")
    print("[AeroNetB API] Frontend served at http://localhost:{port}/")
    app.run(host="0.0.0.0", port=port, debug=True)
