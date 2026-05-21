-- ============================================================
-- AeroNetB Aerospace Supply Chain Management System
-- PostgreSQL DML Script — Dummy Data
-- Student ID: 100774688 | Module: 5CM506 Data Driven Systems
-- Run AFTER ddl.sql
-- ============================================================

-- ============================================================
-- 1. SUPPLIERS
-- ============================================================
INSERT INTO Supplier (business_name, address, country, accreditation_status, contact_email, contact_phone) VALUES
('AeroComponents GmbH',    'Industriestr. 42, Munich, Germany',         'Germany',   'ISO 9001, AS9100',  'procurement@aerocomp.de',      '+49-89-4567891'),
('SkyStar Parts Ltd',      '12 Aviation Way, Bristol, UK',              'UK',        'AS9100, NADCAP',    'supply@skystar.co.uk',          '+44-117-9876543'),
('PrecisionAir Inc.',      '800 Industrial Blvd, Wichita, KS, USA',    'USA',       'ISO 9001, FAA',     'orders@precisionair.com',       '+1-316-5551234'),
('FuselaX S.A.',           'Avenida Industria 5, Madrid, Spain',        'Spain',     'AS9100',            'logistics@fuselax.es',          '+34-91-3456789'),
('AeroFab Technologies',   '45 Composite Ave, Toulouse, France',        'France',    'ISO 9001, EASA',    'contact@aerofab.fr',            '+33-5-61234567');

-- ============================================================
-- 2. PARTS
-- ============================================================
INSERT INTO Part (part_code, part_name, description, category) VALUES
('A320-FP-001',  'A320 Fuselage Panel Aft',        'Aft fuselage skin panel for A320 family aircraft',          'fuselage'),
('A320-WS-002',  'A320 Wing Spar Section',          'Main load-bearing wing spar for A320 centre box',           'wing'),
('B737-FP-003',  'B737 Fuselage Frame Assembly',    'Forward fuselage frame assembly for B737-800',              'fuselage'),
('A350-LP-004',  'A350 Landing Gear Pin',           'High-strength titanium pin for A350 main landing gear',     'landing_gear'),
('B787-EN-005',  'B787 Engine Mount Bracket',       'Composite engine mount bracket for B787 Dreamliner',        'engine');

-- ============================================================
-- 3. PART BASELINE SPECIFICATIONS
-- ============================================================
INSERT INTO PartBaselineSpecification
    (part_id, tensile_strength_mpa, fatigue_limit_mpa, yield_point_mpa, process_details, engineering_references, baseline_notes) VALUES
(1, 620.0,  280.0, 520.0, 'Aluminium 7075-T6. Machined per AMS 2770. Anodised surface finish.', 'DWG-A320-FP-001-Rev4, CAD: /artefacts/a320fp001.stp', 'Must meet AIAG tolerance class B'),
(2, 750.0,  310.0, 680.0, 'Aluminium 7010 billet. Precision milled. Shot-peened per AMS 2430.', 'DWG-A320-WS-002-Rev2, CAD: /artefacts/a320ws002.stp', 'Fatigue test required every 500 units'),
(3, 580.0,  250.0, 490.0, 'Aluminium 2024-T3. Chemical milling. Primed per AMS 3034.',         'DWG-B737-FP-003-Rev7, CAD: /artefacts/b737fp003.stp', 'Corrosion inhibitor coating mandatory'),
(4, 1000.0, 500.0, 930.0, 'Titanium Ti-6Al-4V ELI. CNC machined. Electropolished.',            'DWG-A350-LP-004-Rev1, CAD: /artefacts/a350lp004.stp', 'Non-destructive testing 100% inspection'),
(5, 820.0,  360.0, 740.0, 'Carbon fibre composite layup. Autoclave cured. Ultrasonic inspect.','DWG-B787-EN-005-Rev3, CAD: /artefacts/b787en005.stp', 'Each unit requires individual certification');

-- ============================================================
-- 4. SUPPLIER PART OFFERINGS
-- ============================================================
INSERT INTO SupplierPartOffering (supplier_id, part_id, supplier_part_code, supplier_part_summary, unit_price, lead_time_days) VALUES
(1, 1, 'AC-A320FP-A1', 'Standard offering with anti-corrosion coating and RFID tracking',         12500.00, 45),
(2, 1, 'SS-A320FP-B2', 'Reinforced composite layering with integrated shock sensors in packaging', 13200.00, 50),
(3, 1, 'PA-A320FP-C3', 'Heat-optimised process with 3% lighter material; digital twin included',   11900.00, 42),
(1, 2, 'AC-A320WS-A1', 'Wing spar with enhanced fatigue treatment, serialised tagging',            28000.00, 60),
(4, 2, 'FX-A320WS-D4', 'Standard spar with EASA paperwork package included',                      26500.00, 55),
(3, 3, 'PA-B737FP-C1', 'Chemical milled and primed, bulk packaging option',                       9800.00,  35),
(5, 4, 'AF-A350LP-E1', 'EDM machined titanium pin with full traceability certificate',             4500.00,  20),
(2, 5, 'SS-B787EN-B1', 'Autoclave cured bracket with integrated health monitoring sensor',         31000.00, 70);

-- ============================================================
-- 5. SUPPLIER PART FEATURES
-- ============================================================
INSERT INTO SupplierPartFeature (offering_id, feature_name, feature_description, feature_type) VALUES
(1, 'Anti-corrosion Coating',   'Proprietary zinc-chromate primer applied per AMS 3034',    'coating'),
(1, 'Serialised RFID Tag',      'Embedded RFID for lifecycle tracking throughout service',  'tracking'),
(2, 'Reinforced Composite',     'Additional CFRP layup for higher fatigue resistance',      'structural'),
(2, 'Shock Sensor Packaging',   'Packaging with integrated 3-axis shock sensors for transit','packaging'),
(3, 'Heat-optimised Process',   'Modified heat treatment reducing unit weight by 3%',       'structural'),
(3, 'Digital Twin Data',        'FEA simulation data provided with each delivery',          'tracking'),
(4, 'Enhanced Fatigue Treatment','Additional shot peening cycle for fatigue life extension','structural'),
(7, 'Full Traceability Cert',   'Material batch traceability from raw titanium to finished pin','tracking'),
(8, 'Health Monitoring Sensor', 'Embedded MEMS sensor for in-service vibration monitoring', 'tracking');

-- ============================================================
-- 6. ROLES, PERMISSIONS & ACCESS CONTROL
-- ============================================================
INSERT INTO Role (role_name, description) VALUES
('ProcurementOfficer',  'Manages supplier data, creates and tracks purchase orders'),
('QualityInspector',    'Creates QC reports, validates and certifies delivered components'),
('SupplyChainManager',  'Oversees global shipment flows and supplier performance analytics'),
('EquipmentEngineer',   'Monitors production equipment and analyses IoT sensor feeds'),
('Auditor',             'Read-only access to compliance records, certifications, and audit logs');

INSERT INTO Permission (permission_name, description, access_type) VALUES
('view_suppliers',          'View supplier master data',                    'read'),
('manage_suppliers',        'Create and edit supplier records',             'write'),
('view_orders',             'View purchase orders',                         'read'),
('manage_orders',           'Create and edit purchase orders',              'write'),
('view_shipments',          'View shipment tracking data',                  'read'),
('view_qc_reports',         'View quality control inspection reports',      'read'),
('manage_qc_reports',       'Create and edit QC reports',                  'write'),
('approve_certifications',  'Approve and finalise certification records',   'approve'),
('view_certifications',     'View certification records',                   'read'),
('view_iot_data',           'View IoT device feeds and equipment status',   'read'),
('manage_equipment',        'Edit equipment and IoT device records',        'write'),
('view_audit_logs',         'View audit trail records',                     'audit'),
('view_all_dashboards',     'Access all dashboard panels',                  'read');

-- Role-permission assignments (RBAC matrix)
-- ProcurementOfficer
INSERT INTO RolePermission (role_id, permission_id) VALUES
(1,1),(1,2),(1,3),(1,4),(1,5);
-- QualityInspector
INSERT INTO RolePermission (role_id, permission_id) VALUES
(2,6),(2,7),(2,8),(2,9),(2,3),(2,5);
-- SupplyChainManager
INSERT INTO RolePermission (role_id, permission_id) VALUES
(3,1),(3,3),(3,5),(3,6),(3,9),(3,13);
-- EquipmentEngineer
INSERT INTO RolePermission (role_id, permission_id) VALUES
(4,10),(4,11),(4,3);
-- Auditor
INSERT INTO RolePermission (role_id, permission_id) VALUES
(5,1),(5,3),(5,5),(5,6),(5,9),(5,12),(5,13);

-- ============================================================
-- 7. SYSTEM USERS (passwords are hashed — see setup notes)
-- Plain passwords for demo: Admin1234!, Inspector99!, Manager22!
-- Generated with werkzeug.security.generate_password_hash()
-- ============================================================
INSERT INTO SystemUser (emp_id, full_name, job_title, department, email, phone, access_level, password_hash) VALUES
('EMP-001', 'Sarah Mitchell',   'Procurement Officer',   'Procurement',   'sarah.mitchell@aeronetb.com',   '+44-117-1001', 'write',   'pbkdf2:sha256:600000$salt001$hashedpw001'),
('EMP-002', 'James Nakamura',   'Quality Inspector',     'Quality',       'james.nakamura@aeronetb.com',   '+44-117-1002', 'approve', 'pbkdf2:sha256:600000$salt002$hashedpw002'),
('EMP-003', 'Fatima Al-Rashid', 'Supply Chain Manager',  'Operations',    'fatima.alrashid@aeronetb.com',  '+44-117-1003', 'read',    'pbkdf2:sha256:600000$salt003$hashedpw003'),
('EMP-004', 'David Okafor',     'Equipment Engineer',    'Engineering',   'david.okafor@aeronetb.com',     '+44-117-1004', 'write',   'pbkdf2:sha256:600000$salt004$hashedpw004'),
('EMP-005', 'Elena Vasquez',    'External Auditor',      'Compliance',    'elena.vasquez@regulator.eu',    '+34-91-5001',  'read',    'pbkdf2:sha256:600000$salt005$hashedpw005');

-- User-role assignments
INSERT INTO UserRole (user_id, role_id) VALUES (1,1),(2,2),(3,3),(4,4),(5,5);

-- Role-specific profiles (scenario Section 6 attributes)
INSERT INTO UserRoleProfile (user_id, region_portfolio, authorization_limit,
    inspector_cert_ids, inspection_specialization, digital_signature_ref,
    assigned_product_lines, reporting_level,
    engineering_licence, assigned_facility, iot_device_group_access,
    regulatory_authority, accreditation_licence_id, audit_scope) VALUES
-- Sarah Mitchell – Procurement Officer
(1, 'Europe & MENA',  750000.00, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
-- James Nakamura – Quality Inspector
(2, NULL, NULL, 'NDT-cert-GB-2021, DIM-cert-GB-2022', 'NDT, Dimensional Analysis',
 'SIG-JN-002', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
-- Fatima Al-Rashid – Supply Chain Manager
(3, NULL, NULL, NULL, NULL, NULL, 'Fuselage, Wing Assemblies', 'Global Manager',
 NULL, NULL, NULL, NULL, NULL, NULL),
-- David Okafor – Equipment Engineer
(4, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
 'ENG-LIC-UK-04', 'Bristol Manufacturing Plant A', 'GROUP-A, GROUP-B',
 NULL, NULL, NULL),
-- Elena Vasquez – Auditor
(5, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
 'EASA European Aviation Safety Agency', 'EASA-AUD-2024-885', 'external, safety_certification');

-- ============================================================
-- 8. PURCHASE ORDERS & ORDER LINES
-- ============================================================
INSERT INTO PurchaseOrder (supplier_id, created_by, order_date, desired_delivery_date, actual_delivery_date, status, total_value) VALUES
(1, 1, '2025-10-01', '2025-11-15', '2025-11-12', 'completed',  87500.00),
(2, 1, '2025-10-15', '2025-12-04', '2025-12-06', 'completed',  79200.00),
(3, 1, '2025-11-01', '2026-01-10', NULL,          'dispatched', 59400.00),
(4, 1, '2025-11-20', '2026-02-14', NULL,          'confirmed',  53000.00),
(5, 1, '2025-12-05', '2026-03-01', NULL,          'placed',     62000.00);

INSERT INTO PurchaseOrderLine (order_id, offering_id, quantity, unit_price, line_status) VALUES
(1, 1, 7, 12500.00, 'delivered'),
(2, 2, 6, 13200.00, 'delivered'),
(3, 3, 5, 11900.00, 'shipped'),
(4, 5, 2, 26500.00, 'confirmed'),
(5, 7, 2, 31000.00, 'pending');

-- ============================================================
-- 9. SHIPMENTS & SHIPMENT EVENTS
-- ============================================================
INSERT INTO Shipment (order_id, tracking_number, port_of_entry, eta_date, status) VALUES
(1, 'TRK-20251101-001', 'Port of Southampton, UK',  '2025-11-14', 'delivered'),
(2, 'TRK-20251205-002', 'Port of Felixstowe, UK',   '2025-12-07', 'delivered'),
(3, 'TRK-20260108-003', 'Port of Rotterdam, NL',    '2026-01-10', 'in_transit'),
(4, 'TRK-20260210-004', 'Port of Barcelona, ES',    '2026-02-15', 'in_transit'),
(5, 'TRK-20260228-005', 'Port of Marseille, FR',    '2026-03-02', 'in_transit');

INSERT INTO ShipmentEvent (shipment_id, event_type, event_timestamp, location, condition_notes) VALUES
-- Shipment 1 (completed)
(1, 'departed',        '2025-10-31 08:00:00', 'Munich Freight Terminal, DE',     'All 7 panels loaded, condition good'),
(1, 'arrived_port',    '2025-11-04 14:30:00', 'Calais Port, FR',                 'Container inspected, no damage'),
(1, 'customs_cleared', '2025-11-05 10:00:00', 'Dover Customs, UK',               'HMRC clearance completed'),
(1, 'delivered',       '2025-11-12 09:15:00', 'Bristol Manufacturing Plant A',    'Received in good condition, signed EMP-001'),
-- Shipment 2 (completed)
(2, 'departed',        '2025-11-20 07:00:00', 'Bristol Docks, UK',               'Reinforced packaging, shock sensors active'),
(2, 'arrived_port',    '2025-11-28 16:00:00', 'Felixstowe Container Port, UK',   'No alerts from shock sensors'),
(2, 'delivered',       '2025-12-06 11:30:00', 'Bristol Manufacturing Plant A',    'Minor packaging scuff, contents intact'),
-- Shipment 3 (in transit)
(3, 'departed',        '2026-01-03 06:30:00', 'Wichita Air Freight, USA',        '5 panels on 2 pallets'),
(3, 'arrived_port',    '2026-01-07 20:00:00', 'Rotterdam Port, NL',              'Awaiting customs clearance'),
-- Shipment 4 (in transit, delayed)
(4, 'departed',        '2026-01-25 09:00:00', 'Madrid Industrial Hub, ES',       'Order confirmed and loaded'),
-- Shipment 5 (in transit)
(5, 'departed',        '2026-02-20 08:00:00', 'Toulouse Aerospace Logistics, FR','Composite brackets in climate-controlled container');

-- ============================================================
-- 10. DELIVERED ITEMS (traceability bridge)
-- ============================================================
INSERT INTO DeliveredItem (line_id, shipment_id, serial_number, batch_number, delivery_timestamp, condition_on_arrival) VALUES
(1, 1, 'SN-A320FP-001-001', 'BATCH-AC-2025-OCT-07', '2025-11-12 09:15:00', 'good'),
(1, 1, 'SN-A320FP-001-002', 'BATCH-AC-2025-OCT-07', '2025-11-12 09:15:00', 'good'),
(1, 1, 'SN-A320FP-001-003', 'BATCH-AC-2025-OCT-07', '2025-11-12 09:15:00', 'good'),
(2, 2, 'SN-A320FP-002-001', 'BATCH-SS-2025-NOV-06', '2025-12-06 11:30:00', 'good'),
(2, 2, 'SN-A320FP-002-002', 'BATCH-SS-2025-NOV-06', '2025-12-06 11:30:00', 'good');

-- ============================================================
-- 11. EQUIPMENT & IoT DEVICES
-- ============================================================
INSERT INTO Equipment (equipment_name, equipment_type, facility, manufacturer, installation_date, status) VALUES
('CNC Mill Alpha-7',       'CNC',          'Bristol Plant A',  'Mazak Corporation',    '2020-03-15', 'operational'),
('Autoclave Unit B-2',     'autoclave',    'Bristol Plant A',  'Scholz Autoclave',     '2019-07-22', 'operational'),
('Transit Container TC-9', 'container',    'Logistics Hub',    'Thermo King',          '2022-01-10', 'operational'),
('Heat Treatment Furnace', 'oven',         'Bristol Plant B',  'Ipsen Technologies',   '2018-11-05', 'maintenance'),
('Ultrasonic NDT Station', 'NDT',          'Quality Lab',      'Olympus Corporation',  '2021-06-30', 'operational');

INSERT INTO IoTDevice (equipment_id, device_identifier, device_type, sensor_types) VALUES
(1, 'IOT-CNC-A7-T01',  'temperature_sensor',  'temperature,vibration'),
(1, 'IOT-CNC-A7-V01',  'vibration_monitor',   'vibration,cycle_count'),
(2, 'IOT-AC-B2-T01',   'temperature_sensor',  'temperature,pressure'),
(3, 'IOT-TC9-GPS-01',  'gps_tracker',         'temperature,gps,shock'),
(4, 'IOT-HTF-T01',     'temperature_sensor',  'temperature'),
(5, 'IOT-NDT-S01',     'status_sensor',       'vibration,cycle_count');

-- ============================================================
-- 12. ENGINEERING ARTEFACTS (unstructured data references)
-- ============================================================
INSERT INTO EngineeringArtefact (part_id, artefact_type, file_name, storage_reference, file_size_kb, uploaded_by, description) VALUES
(1, 'CAD',     'a320_fuselage_panel_rev4.stp',   '/storage/cad/a320fp001/rev4.stp',      15200, 4, 'STEP file for A320 fuselage panel Revision 4'),
(1, 'drawing', 'a320_fuselage_panel_dwg_rev4.pdf','/storage/drawings/a320fp001_rev4.pdf', 3400,  4, 'Engineering drawing with GD&T tolerances'),
(2, 'CAD',     'a320_wing_spar_rev2.stp',        '/storage/cad/a320ws002/rev2.stp',      22100, 4, 'STEP file for A320 wing spar section'),
(4, 'PDF',     'a350_lp_material_cert.pdf',      '/storage/certs/a350lp004_mat.pdf',     890,   2, 'Raw titanium material certificate, batch TI-2025-09'),
(5, 'simulation_data', 'b787_engine_mount_fea.zip', '/storage/sim/b787en005_fea.zip',   45000, 4, 'FEA simulation dataset provided by AeroFab with delivery');

-- ============================================================
-- 13. AUDIT LOG SEED ENTRIES
-- ============================================================
INSERT INTO AuditLog (user_id, action_type, entity_type, entity_id, description, ip_address, outcome) VALUES
(1, 'LOGIN',  'SystemUser',   1, 'User sarah.mitchell@aeronetb.com logged in',                  '192.168.1.10', 'success'),
(1, 'CREATE', 'PurchaseOrder',1, 'Created purchase order PO-1 for supplier AeroComponents GmbH','192.168.1.10', 'success'),
(2, 'LOGIN',  'SystemUser',   2, 'User james.nakamura@aeronetb.com logged in',                  '192.168.1.20', 'success'),
(2, 'CREATE', 'QCReport',     1, 'Created QC report QC-784512-A1 for delivered item DI-1',      '192.168.1.20', 'success'),
(2, 'APPROVE','CertRecord',   1, 'Approved certification record CERT-2025-001',                  '192.168.1.20', 'success'),
(3, 'VIEW',   'Dashboard',    NULL,'Supply chain manager viewed supplier KPI dashboard',          '192.168.1.30', 'success'),
(5, 'VIEW',   'CertRecord',   1, 'Auditor viewed certification record CERT-2025-001 (read-only)','192.168.1.50', 'success');

-- End of DML Script
