-- ============================================================
-- AeroNetB Aerospace Supply Chain Management System
-- PostgreSQL DDL Script
-- Student ID: 100774688 | Module: 5CM506 Data Driven Systems
-- ============================================================

-- Drop tables in reverse dependency order (safe re-run)
DROP TABLE IF EXISTS EngineeringArtefact    CASCADE;
DROP TABLE IF EXISTS IoTDevice              CASCADE;
DROP TABLE IF EXISTS Equipment              CASCADE;
DROP TABLE IF EXISTS AuditLog               CASCADE;
DROP TABLE IF EXISTS UserRoleProfile        CASCADE;
DROP TABLE IF EXISTS RolePermission         CASCADE;
DROP TABLE IF EXISTS UserRole               CASCADE;
DROP TABLE IF EXISTS Permission             CASCADE;
DROP TABLE IF EXISTS Role                   CASCADE;
DROP TABLE IF EXISTS SystemUser             CASCADE;
DROP TABLE IF EXISTS DeliveredItem          CASCADE;
DROP TABLE IF EXISTS ShipmentEvent          CASCADE;
DROP TABLE IF EXISTS Shipment               CASCADE;
DROP TABLE IF EXISTS PurchaseOrderLine      CASCADE;
DROP TABLE IF EXISTS PurchaseOrder          CASCADE;
DROP TABLE IF EXISTS SupplierPartFeature    CASCADE;
DROP TABLE IF EXISTS SupplierPartOffering   CASCADE;
DROP TABLE IF EXISTS PartBaselineSpecification CASCADE;
DROP TABLE IF EXISTS Part                   CASCADE;
DROP TABLE IF EXISTS Supplier               CASCADE;

-- ============================================================
-- 1. SUPPLIER & PART MASTER DATA
-- ============================================================

CREATE TABLE Supplier (
    supplier_id         SERIAL          PRIMARY KEY,
    business_name       VARCHAR(200)    NOT NULL,
    address             TEXT,
    country             VARCHAR(100),
    accreditation_status VARCHAR(100),  -- e.g. ISO 9001, AS9100
    contact_email       VARCHAR(200),
    contact_phone       VARCHAR(50),
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Part (
    part_id             SERIAL          PRIMARY KEY,
    part_code           VARCHAR(100)    UNIQUE NOT NULL,
    part_name           VARCHAR(200)    NOT NULL,
    description         TEXT,
    category            VARCHAR(100),   -- fuselage, wing, engine, landing_gear
    created_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Separated from Part: engineering specification is a distinct concern (3NF)
-- Avoids embedding heavyweight technical fields in the core part identity record
CREATE TABLE PartBaselineSpecification (
    spec_id                 SERIAL          PRIMARY KEY,
    part_id                 INT             UNIQUE NOT NULL REFERENCES Part(part_id) ON DELETE CASCADE,
    tensile_strength_mpa    DECIMAL(10,2),
    fatigue_limit_mpa       DECIMAL(10,2),
    yield_point_mpa         DECIMAL(10,2),
    process_details         TEXT,           -- heat treatment, machining steps
    engineering_references  TEXT,           -- CAD model refs, drawing numbers
    baseline_notes          TEXT,
    created_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Resolves the many-to-many between Supplier and Part
-- One supplier may offer many parts; one part may be sourced from many suppliers
CREATE TABLE SupplierPartOffering (
    offering_id             SERIAL          PRIMARY KEY,
    supplier_id             INT             NOT NULL REFERENCES Supplier(supplier_id),
    part_id                 INT             NOT NULL REFERENCES Part(part_id),
    supplier_part_code      VARCHAR(100),
    supplier_part_summary   TEXT,
    unit_price              DECIMAL(12,2),
    lead_time_days          INT,
    status                  VARCHAR(50)     NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active','suspended','discontinued')),
    UNIQUE (supplier_id, part_id)
);

-- Kept relational (not embedded) so individual features can be queried & compared
CREATE TABLE SupplierPartFeature (
    feature_id              SERIAL          PRIMARY KEY,
    offering_id             INT             NOT NULL REFERENCES SupplierPartOffering(offering_id) ON DELETE CASCADE,
    feature_name            VARCHAR(200)    NOT NULL,
    feature_description     TEXT,
    feature_type            VARCHAR(100)    -- coating, structural, tracking, packaging
);

-- ============================================================
-- 2. ACCESS CONTROL (RBAC)
-- ============================================================

CREATE TABLE Role (
    role_id     SERIAL          PRIMARY KEY,
    role_name   VARCHAR(100)    UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE Permission (
    permission_id   SERIAL          PRIMARY KEY,
    permission_name VARCHAR(100)    UNIQUE NOT NULL,
    description     TEXT,
    access_type     VARCHAR(50)     NOT NULL CHECK (access_type IN ('read','write','approve','audit'))
);

CREATE TABLE SystemUser (
    user_id         SERIAL          PRIMARY KEY,
    emp_id          VARCHAR(50)     UNIQUE NOT NULL,
    full_name       VARCHAR(200)    NOT NULL,
    job_title       VARCHAR(100),
    department      VARCHAR(100),
    email           VARCHAR(200)    UNIQUE NOT NULL,
    phone           VARCHAR(50),
    access_level    VARCHAR(50),
    password_hash   VARCHAR(255)    NOT NULL,
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many: a user may hold multiple roles
CREATE TABLE UserRole (
    user_role_id    SERIAL      PRIMARY KEY,
    user_id         INT         NOT NULL REFERENCES SystemUser(user_id) ON DELETE CASCADE,
    role_id         INT         NOT NULL REFERENCES Role(role_id) ON DELETE CASCADE,
    assigned_at     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, role_id)
);

-- Many-to-many: a role carries multiple permissions
CREATE TABLE RolePermission (
    rp_id           SERIAL      PRIMARY KEY,
    role_id         INT         NOT NULL REFERENCES Role(role_id) ON DELETE CASCADE,
    permission_id   INT         NOT NULL REFERENCES Permission(permission_id) ON DELETE CASCADE,
    UNIQUE (role_id, permission_id)
);

-- Scenario Section 6: role-specific extended attributes per user
-- Nullable fields allow a single table to cover all five role types
CREATE TABLE UserRoleProfile (
    profile_id                  SERIAL          PRIMARY KEY,
    user_id                     INT             UNIQUE NOT NULL REFERENCES SystemUser(user_id) ON DELETE CASCADE,
    -- Procurement Officer
    region_portfolio            VARCHAR(200),
    authorization_limit         DECIMAL(12,2),
    -- Quality Inspector
    inspector_cert_ids          TEXT,           -- e.g. NDT-cert-001, DIM-cert-002
    inspection_specialization   VARCHAR(200),   -- NDT, dimensional, environmental
    digital_signature_ref       VARCHAR(500),
    -- Supply Chain Manager
    assigned_product_lines      VARCHAR(200),   -- fuselage, wing assemblies
    reporting_level             VARCHAR(100),   -- regional, global
    -- Equipment Engineer
    engineering_licence         VARCHAR(100),
    assigned_facility           VARCHAR(200),
    iot_device_group_access     TEXT,           -- machine groups under responsibility
    -- Auditor / Regulator
    regulatory_authority        VARCHAR(200),
    accreditation_licence_id    VARCHAR(100),
    audit_scope                 VARCHAR(200)    -- internal, external, safety_certification
);

-- Audit log: every data access and modification attributed to an empId
-- Kept relational because accountability queries must be filterable by user/time
CREATE TABLE AuditLog (
    audit_id    SERIAL          PRIMARY KEY,
    user_id     INT             REFERENCES SystemUser(user_id),
    action_type VARCHAR(100)    NOT NULL,   -- LOGIN, CREATE, UPDATE, DELETE, VIEW, APPROVE
    entity_type VARCHAR(100),              -- Supplier, PurchaseOrder, QCReport, etc.
    entity_id   INT,
    description TEXT,
    ip_address  VARCHAR(50),
    outcome     VARCHAR(50)     DEFAULT 'success' CHECK (outcome IN ('success','failure','warning')),
    created_at  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. PROCUREMENT & LOGISTICS
-- ============================================================

CREATE TABLE PurchaseOrder (
    order_id                SERIAL          PRIMARY KEY,
    supplier_id             INT             NOT NULL REFERENCES Supplier(supplier_id),
    created_by              INT             REFERENCES SystemUser(user_id),
    order_date              DATE            NOT NULL,
    desired_delivery_date   DATE,
    actual_delivery_date    DATE,
    status                  VARCHAR(50)     NOT NULL DEFAULT 'placed'
                            CHECK (status IN ('placed','confirmed','dispatched','delivered','completed')),
    total_value             DECIMAL(12,2),
    notes                   TEXT,
    created_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE PurchaseOrderLine (
    line_id         SERIAL          PRIMARY KEY,
    order_id        INT             NOT NULL REFERENCES PurchaseOrder(order_id) ON DELETE CASCADE,
    offering_id     INT             NOT NULL REFERENCES SupplierPartOffering(offering_id),
    quantity        INT             NOT NULL CHECK (quantity > 0),
    unit_price      DECIMAL(12,2),
    line_status     VARCHAR(50)     NOT NULL DEFAULT 'pending'
                    CHECK (line_status IN ('pending','confirmed','shipped','delivered'))
);

CREATE TABLE Shipment (
    shipment_id     SERIAL          PRIMARY KEY,
    order_id        INT             NOT NULL REFERENCES PurchaseOrder(order_id),
    tracking_number VARCHAR(100),
    port_of_entry   VARCHAR(200),
    eta_date        DATE,
    status          VARCHAR(50)     NOT NULL DEFAULT 'in_transit'
                    CHECK (status IN ('in_transit','arrived_port','customs','delivered','delayed')),
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Time-stamped progression records for each shipment lifecycle stage
CREATE TABLE ShipmentEvent (
    event_id            SERIAL          PRIMARY KEY,
    shipment_id         INT             NOT NULL REFERENCES Shipment(shipment_id) ON DELETE CASCADE,
    event_type          VARCHAR(100)    NOT NULL,   -- departed, arrived_port, customs_cleared, delivered
    event_timestamp     TIMESTAMP       NOT NULL,
    location            VARCHAR(200),
    condition_notes     TEXT
);

-- Critical traceability bridge: links received physical items to procurement + logistics
-- Quality control and certification apply to DeliveredItem, not to abstract order lines
CREATE TABLE DeliveredItem (
    delivered_item_id   SERIAL          PRIMARY KEY,
    line_id             INT             NOT NULL REFERENCES PurchaseOrderLine(line_id),
    shipment_id         INT             NOT NULL REFERENCES Shipment(shipment_id),
    serial_number       VARCHAR(100),
    batch_number        VARCHAR(100),
    delivery_timestamp  TIMESTAMP,
    condition_on_arrival VARCHAR(100)   DEFAULT 'good'
                        CHECK (condition_on_arrival IN ('good','damaged','quarantine','rejected'))
);

-- ============================================================
-- 4. MANUFACTURING EQUIPMENT & IoT DEVICES
-- ============================================================

CREATE TABLE Equipment (
    equipment_id        SERIAL          PRIMARY KEY,
    equipment_name      VARCHAR(200)    NOT NULL,
    equipment_type      VARCHAR(100),   -- CNC, press, oven, container
    facility            VARCHAR(200),
    manufacturer        VARCHAR(200),
    installation_date   DATE,
    status              VARCHAR(50)     NOT NULL DEFAULT 'operational'
                        CHECK (status IN ('operational','maintenance','offline','decommissioned'))
);

-- One equipment unit can have multiple IoT sensors attached
CREATE TABLE IoTDevice (
    device_id           SERIAL          PRIMARY KEY,
    equipment_id        INT             NOT NULL REFERENCES Equipment(equipment_id) ON DELETE CASCADE,
    device_identifier   VARCHAR(100)    UNIQUE NOT NULL,
    device_type         VARCHAR(100),   -- temperature_sensor, vibration_monitor, gps_tracker
    sensor_types        TEXT,           -- comma-separated: temperature,vibration,pressure,gps
    status              VARCHAR(50)     NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','inactive','fault'))
);

-- ============================================================
-- 5. ENGINEERING ARTEFACTS (unstructured data reference model)
-- Metadata + storage references for CAD files, PDFs, drawings, images
-- Actual binaries stored externally; this table preserves structured linkage
-- ============================================================

CREATE TABLE EngineeringArtefact (
    artefact_id         SERIAL          PRIMARY KEY,
    part_id             INT             REFERENCES Part(part_id),
    delivered_item_id   INT             REFERENCES DeliveredItem(delivered_item_id),
    artefact_type       VARCHAR(100)    NOT NULL
                        CHECK (artefact_type IN ('CAD','PDF','image','drawing','3D_model','simulation_data')),
    file_name           VARCHAR(300),
    storage_reference   VARCHAR(500),   -- file path or cloud object storage URL
    file_size_kb        INT,
    uploaded_by         INT             REFERENCES SystemUser(user_id),
    description         TEXT,
    uploaded_at         TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 6. INDEXES (performance for common query patterns)
-- ============================================================

CREATE INDEX idx_spo_supplier      ON SupplierPartOffering(supplier_id);
CREATE INDEX idx_spo_part          ON SupplierPartOffering(part_id);
CREATE INDEX idx_po_supplier       ON PurchaseOrder(supplier_id);
CREATE INDEX idx_po_status         ON PurchaseOrder(status);
CREATE INDEX idx_po_order_date     ON PurchaseOrder(order_date);
CREATE INDEX idx_pol_order         ON PurchaseOrderLine(order_id);
CREATE INDEX idx_shipment_order    ON Shipment(order_id);
CREATE INDEX idx_shipment_status   ON Shipment(status);
CREATE INDEX idx_event_shipment    ON ShipmentEvent(shipment_id);
CREATE INDEX idx_event_timestamp   ON ShipmentEvent(event_timestamp);
CREATE INDEX idx_delivered_line    ON DeliveredItem(line_id);
CREATE INDEX idx_iotdevice_equip   ON IoTDevice(equipment_id);
CREATE INDEX idx_auditlog_user     ON AuditLog(user_id);
CREATE INDEX idx_auditlog_time     ON AuditLog(created_at);
CREATE INDEX idx_auditlog_entity   ON AuditLog(entity_type, entity_id);

-- End of DDL Script
