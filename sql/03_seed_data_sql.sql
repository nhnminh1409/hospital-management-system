USE hospital_db;

-- ======================================================
-- REFERENCE DATA
-- ======================================================
INSERT INTO roles (role_id, role_name) VALUES 
(1, 'Admin'), (2, 'Doctor'), (3, 'Receptionist'), (4, 'Accountant'), (5, 'Human Resource (HR)');

INSERT INTO departments (dept_id, dept_name) VALUES 
(1, 'Internal Medicine'), (2, 'Pediatrics'), (3, 'Obstetrics and Gynecology'), 
(4, 'Otolaryngology'), (5, 'General Surgery'), (6, 'Dermatology'), (7, 'Administration');

-- ======================================================
-- 3. USERS (22 Accounts)
-- ======================================================
INSERT INTO users (user_id, username, password_hash, role_id) VALUES 
(1, 'recep_alice', 'hash123', 3),
(2, 'acc_bob', 'hash123', 4),
(23, 'admin_super', 'super_secure_hash_123', 1),
(25, 'hr_alima', 'hr123',5);

-- Users for 20 Doctors (IDs 3 to 22)
INSERT INTO users (user_id, username, password_hash, role_id)
SELECT n, CONCAT('dr_', LOWER(REPLACE(name, ' ', '_'))), 'hash123', 2
FROM (
    SELECT 3 AS n, 'James Wilson' AS name UNION ALL SELECT 4, 'Mary Pemberton' UNION ALL
    SELECT 5, 'Robert Brown' UNION ALL SELECT 6, 'Patricia Garcia' UNION ALL
    SELECT 7, 'Michael Miller' UNION ALL SELECT 8, 'Linda Davis' UNION ALL
    SELECT 9, 'William Rodriguez' UNION ALL SELECT 10, 'Barbara Martinez' UNION ALL
    SELECT 11, 'David Hernandez' UNION ALL SELECT 12, 'Susan Lopez' UNION ALL
    SELECT 13, 'Charles Gonzalez' UNION ALL SELECT 14, 'Jessica Wilson' UNION ALL
    SELECT 15, 'Christopher Anderson' UNION ALL SELECT 16, 'Sarah Thomas' UNION ALL
    SELECT 17, 'Daniel Taylor' UNION ALL SELECT 18, 'Karen Moore' UNION ALL
    SELECT 19, 'Matthew Jackson' UNION ALL SELECT 20, 'Nancy White' UNION ALL
    SELECT 21, 'Anthony Harris' UNION ALL SELECT 22, 'Lisa Martin'
) AS doctor_names;

-- ======================================================
-- 4. STAFF (22 Members with Real Names)
-- ======================================================
INSERT INTO staff (staff_id, full_name, dob, gender, phone_number, email, user_id, dept_id) VALUES 
(1, 'Alice Smith', '1995-02-10', 'Female', '0911000001', 'alice@hosp.com', 1, 7),
(2, 'Bob Johnson', '1990-05-15', 'Male', '0911000002', 'bob@hosp.com', 2, 7),
(3, 'James Wilson', '1975-01-10', 'Male', '0911000003', 'james.w@hosp.com', 3, 1),
(4, 'Mary Pemberton', '1982-03-22', 'Female', '0911000004', 'mary.p@hosp.com', 4, 1),
(5, 'Robert Brown', '1978-11-05', 'Male', '0911000005', 'robert.b@hosp.com', 5, 1),
(6, 'Patricia Garcia', '1985-07-14', 'Female', '0911000006', 'patricia.g@hosp.com', 6, 2),
(7, 'Michael Miller', '1980-09-30', 'Male', '0911000007', 'michael.m@hosp.com', 7, 2),
(8, 'Linda Davis', '1983-12-12', 'Female', '0911000008', 'linda.d@hosp.com', 8, 2),
(9, 'William Rodriguez', '1976-04-25', 'Male', '0911000009', 'william.r@hosp.com', 9, 2),
(10, 'Barbara Martinez', '1988-02-28', 'Female', '0911000010', 'barbara.m@hosp.com', 10, 3),
(11, 'David Hernandez', '1979-06-18', 'Male', '0911000011', 'david.h@hosp.com', 11, 3),
(12, 'Susan Lopez', '1984-08-08', 'Female', '0911000012', 'susan.l@hosp.com', 12, 3),
(13, 'Charles Gonzalez', '1977-10-20', 'Male', '0911000013', 'charles.g@hosp.com', 13, 3),
(14, 'Jessica Wilson', '1986-01-05', 'Female', '0911000014', 'jessica.w@hosp.com', 14, 4),
(15, 'Christopher Anderson', '1981-03-15', 'Male', '0911000015', 'chris.a@hosp.com', 15, 4),
(16, 'Sarah Thomas', '1989-05-25', 'Female', '0911000016', 'sarah.t@hosp.com', 16, 4),
(17, 'Daniel Taylor', '1974-07-07', 'Male', '0911000017', 'daniel.t@hosp.com', 17, 5),
(18, 'Karen Moore', '1987-09-09', 'Female', '0911000018', 'karen.m@hosp.com', 18, 5),
(19, 'Matthew Jackson', '1982-11-11', 'Male', '0911000019', 'matthew.j@hosp.com', 19, 5),
(20, 'Nancy White', '1979-01-20', 'Female', '0911000020', 'nancy.w@hosp.com', 20, 6),
(21, 'Anthony Harris', '1985-04-12', 'Male', '0911000021', 'anthony.h@hosp.com', 21, 6),
(22, 'Lisa Martin', '1983-06-30', 'Female', '0911000022', 'lisa.m@hosp.com', 22, 6),
(23, 'Justin Bieber', '1990-07-24', 'Male', '0823468445', 'justin.b@hosp.com',23,7),
(25, 'Alice Mason', '1995-08-10', 'Female', '091100456', 'alima@hosp.com', 25, 7);

-- ======================================================
-- 5. DOCTORS (20 Doctors assigned to 6 Specialties)
-- ======================================================
INSERT INTO doctors (doctor_id, staff_id, specialty) VALUES 
(1, 3, 'Internal Medicine'), (2, 4, 'Internal Medicine'), (3, 5, 'Internal Medicine'),
(4, 6, 'Pediatrics'), (5, 7, 'Pediatrics'), (6, 8, 'Pediatrics'), (7, 9, 'Pediatrics'),
(8, 10, 'Obstetrics and Gynecology'), (9, 11, 'Obstetrics and Gynecology'), (10, 12, 'Obstetrics and Gynecology'), (11, 13, 'Obstetrics and Gynecology'),
(12, 14, 'Otolaryngology'), (13, 15, 'Otolaryngology'), (14, 16, 'Otolaryngology'),
(15, 17, 'General Surgery'), (16, 18, 'General Surgery'), (17, 19, 'General Surgery'),
(18, 20, 'Dermatology'), (19, 21, 'Dermatology'), (20, 22, 'Dermatology');

-- ======================================================
-- 6. PATIENTS (20 Patients)
-- ======================================================
INSERT INTO patients (patient_id, full_name, dob, gender, phone, email) VALUES 
(1, 'John Doe', '1990-01-01', 'Male', '0310000001', 'john@example.com'),
(2, 'Jane Smith', '1992-05-15', 'Female', '0310000002', 'jane@example.com'),
(3, 'Michael Johnson', '1985-11-20', 'Male', '0310000003', 'mike@example.com'),
(4, 'Emily Williams', '1998-03-10', 'Female', '0310000004', 'emily@example.com'),
(5, 'David Brown', '1975-07-25', 'Male', '0310000005', 'david@example.com'),
(6, 'Sarah Miller', '2005-09-12', 'Female', '0310000006', 'sarah@example.com'),
(7, 'James Davis', '1988-12-30', 'Male', '0310000007', 'james@example.com'),
(8, 'Linda Wilson', '1993-02-14', 'Female', '0310000008', 'linda@example.com'),
(9, 'Robert Moore', '1980-06-05', 'Male', '0310000009', 'robert@example.com'),
(10, 'Karen Taylor', '1995-10-22', 'Female', '0310000010', 'karen@example.com'),
(11, 'William Anderson', '1970-04-18', 'Male', '0310000011', 'will@example.com'),
(12, 'Jessica Thomas', '2001-08-08', 'Female', '0310000012', 'jess@example.com'),
(13, 'Christopher Lee', '1982-12-12', 'Male', '0310000013', 'chris@example.com'),
(14, 'Margaret White', '1996-01-05', 'Female', '0310000014', 'margaret@example.com'),
(15, 'Thomas Harris', '1984-03-15', 'Male', '0310000015', 'thomas@example.com'),
(16, 'Ashley Martin', '1989-05-25', 'Female', '0310000016', 'ashley@example.com'),
(17, 'Matthew Garcia', '1974-07-07', 'Male', '0310000017', 'matt@example.com'),
(18, 'Kimberly Martinez', '1987-09-09', 'Female', '0310000018', 'kim@example.com'),
(19, 'Andrew Robinson', '1982-11-11', 'Male', '0310000019', 'andrew@example.com'),
(20, 'Donna Clark', '1979-01-20', 'Female', '0310000020', 'donna@example.com');

USE hospital_db;

-- ======================================================
-- 7. PATIENT HEALTH PROFILES (20 Profiles)
-- ======================================================
INSERT INTO patient_health_profile (profile_id,patient_id, allergies, chronic_diseases, blood_type) VALUES 
(1,1, 'Peanuts', 'Hypertension', 'O+'),
(2,2, 'None', 'None', 'A+'),
(3,3, 'Penicillin', 'Diabetes Type 2', 'B-'),
(4,4, 'Pollen', 'Asthma', 'O-'),
(5,5, 'None', 'Heart Disease', 'AB+'),
(6,6, 'Seafood', 'None', 'A-'),
(7,7, 'Dust Mites', 'None', 'B+'),
(8,8, 'None', 'Chronic Kidney Disease', 'O+'),
(9,9, 'Aspirin', 'None', 'AB-'),
(10,10, 'None', 'None', 'A+'),
(11,11, 'Lactose', 'Hypertension', 'B+'),
(12,12, 'None', 'None', 'O+'),
(13,13, 'None', 'Asthma', 'A+'),
(14, 14, 'Sulfa drugs', 'None', 'B-'),
(15, 15, 'None', 'Diabetes Type 1', 'O-'),
(16, 16, 'Bee stings', 'None', 'AB+'),
(17, 17, 'None', 'Hyperthyroidism', 'A-'),
(18, 18, 'None', 'None', 'B+'),
(19, 19, 'Shellfish', 'None', 'O+'),
(20, 20, 'None', 'Chronic Gastritis', 'AB-');
-- ======================================================
-- 8. DEMO APPOINTMENTS
-- ======================================================
INSERT INTO appointments (appt_id, patient_id, doctor_id, appt_date, status) VALUES 
(1, 1, 1, '2026-04-30 08:30:00', 'Completed'),
(2, 2, 4, '2026-04-30 09:15:00', 'Scheduled'),
(3, 3, 8, '2026-05-01 10:00:00', 'Scheduled');
-- ======================================================
-- 9. ROOM
-- ======================================================
USE hospital_db;
INSERT INTO rooms (room_id, room_name, dept_id) VALUES 
(101, 'Room 101', 1),
(102, 'Room 102', 1),
(103, 'Room 103', 2),
(201, 'Room 201', 3),
(202, 'Room 202', 3),
(203, 'Room 203', 4),
(301, 'Room 301', 5),
(302, 'Room 302', 5),
(303, 'Room 303', 6),
(304, 'Room 304', 6);

-- ======================================================
-- 10. BEDS
-- ======================================================
INSERT INTO beds (bed_id, bed_code, room_id, status) VALUES
(1, 'B101-1', 101, 'Available'),
(2, 'B101-2', 101, 'Available'),
(3, 'B102-1', 102, 'Available'),
(4, 'B103-1', 103, 'Available'),
(5, 'B201-1', 201, 'Available'),
(6, 'B202-1', 202, 'Occupied'),
(7, 'B203-1', 203, 'Occupied'),
(8, 'B301-1', 301, 'Occupied'),
(9, 'B302-1', 302, 'Occupied'),
(10, 'B303-1', 303, 'Maintenance');
-- ======================================================
-- 11. ADMISSIONS
-- ======================================================
-- 1. Patients who have completed treatment and been discharged from the hospital
INSERT INTO admissions (patient_id, doctor_id, bed_id, admission_date, discharge_date, discharge_status) VALUES
(6, 1,  1, '2023-10-01 08:30:00', '2023-10-10 14:00:00', 'Discharged'),
(7, 2,  2, '2023-10-05 10:15:00', '2023-10-12 09:30:00', 'Discharged'),
(8, 15, 3, '2023-10-15 22:00:00', '2023-10-20 16:45:00', 'Discharged'),
(4, 4,  5, '2023-11-02 07:00:00', '2023-11-05 11:00:00', 'Discharged'),
(5, 5,  4, '2023-11-10 13:20:00', '2023-11-15 08:00:00', 'Discharged');

-- 2. Cases currently under hospital treatment (discharge_date is NULL)
INSERT INTO admissions (patient_id, doctor_id, bed_id, admission_date, discharge_date, discharge_status) VALUES
(11, 3,  6, '2023-12-01 09:00:00', NULL, 'Admitted'),
(12, 8,  7, '2023-12-03 14:30:00', NULL, 'Admitted'),
(13, 9,  8, '2023-12-04 16:00:00', NULL, 'Admitted'),
(10, 10, 9, '2023-12-05 23:45:00', NULL, 'Admitted');

-- ======================================================
-- 12. MEDICINES & CATEGORIES
-- ======================================================
INSERT INTO medicine_categories (category_name) VALUES 
('Antibiotics'), ('Analgesics'), ('Antipyretics'), ('Vitamins'), ('Antacids');

INSERT INTO medicines (med_id, med_name, category_id, price, stock) VALUES 
(1001, 'Amoxicillin', 1, 10.50, 200),
(1002, 'Paracetamol', 2, 2.00, 500),
(1003, 'Ibuprofen', 2, 5.75, 300),
(1004, 'Vitamin D3', 4, 15.00, 150),
(1005, 'Gaviscon', 5, 8.20, 100);

-- ======================================================
-- 13. MEDICAL RECORDS (Sample Clinical Data)
-- ======================================================
INSERT INTO medical_records 
(record_id, appt_id, admission_id, symptoms, diagnosis, doctor_notes) 
VALUES 
(1,1, NULL, 'Sore throat, fever', 'Acute Pharyngitis', 'Antibiotics prescribed'),
(2,2, NULL, 'Fever, fatigue', 'Mild Influenza', 'Rest and fluids'),
(3,3, NULL, 'Post-surgery pain', 'Recovery', 'Monitor healing');
-- ======================================================
-- 14. PRESCRIPTIONS & DETAILS
-- ======================================================
INSERT INTO prescriptions (presc_id, record_id, doctor_id) VALUES 
(1, 1, 1),
(2, 2, 4);

INSERT INTO presc_details (detail_id, presc_id, med_id, dosage, quantity) VALUES 
(1, 1, 1001, '500mg, twice daily after meals', 14),
(2, 2, 1002, '500mg, every 6 hours if feverish', 10);

-- ======================================================
-- 15. INSURANCE (Health Insurance for Selected Patients)
-- ======================================================
INSERT INTO insurance (insurance_id, patient_id, coverage_rate, expiry_date, provider) VALUES
('INS-2024-001', 1,  0.80, '2027-12-31', 'VietLife Insurance'),
('INS-2024-002', 3,  0.70, '2026-06-30', 'Bao Viet Health'),
('INS-2024-003', 5,  0.90, '2025-12-31', 'PVI Insurance'),
('INS-2024-004', 8,  0.75, '2027-03-15', 'AIA Vietnam'),
('INS-2024-005', 10, 0.60, '2026-09-01', 'Prudential Health'),
('INS-2024-006', 11, 0.85, '2028-01-01', 'VietLife Insurance'),
('INS-2024-007', 13, 0.50, '2026-12-31', 'Bao Viet Health'),
('INS-2024-008', 15, 0.65, '2027-06-30', 'Manulife Vietnam'),
('INS-2024-009', 17, 0.80, '2026-04-01', 'Sun Life Vietnam'),
('INS-2024-010', 19, 0.70, '2025-08-15', 'AIA Vietnam');

-- ======================================================
-- 16. INVOICES (Billing for Appointments & Admissions)
-- ======================================================
-- NOTE: Invoices for appointments are AUTO-CREATED by trigger trg_create_invoice_on_appointment.
-- Do NOT insert manually for appt_id rows — instead UPDATE the auto-generated invoice.

-- Mark appointment 1's invoice as Paid (auto-created as Unpaid by trigger)
UPDATE invoices SET payment_status = 'Paid', total_amount = 250000.00, invoice_date = '2026-04-30 10:15:00'
WHERE appt_id = 1;

-- Invoices for discharged admissions (admission_id 1-5)
INSERT INTO invoices (appt_id, admission_id, invoice_date, total_amount, payment_status) VALUES
(NULL, 1, '2023-10-10 15:00:00', 3200000.00, 'Paid'),
(NULL, 2, '2023-10-12 10:30:00', 2750000.00, 'Paid'),
(NULL, 3, '2023-10-20 17:00:00', 5100000.00, 'Paid'),
(NULL, 4, '2023-11-05 12:00:00', 1800000.00, 'Paid'),
(NULL, 5, '2023-11-15 09:00:00', 4300000.00, 'Unpaid');

-- Invoices for currently admitted patients (pending payment)
INSERT INTO invoices (appt_id, admission_id, invoice_date, total_amount, payment_status) VALUES
(NULL, 6, '2023-12-01 10:00:00', 0.00, 'Unpaid'),
(NULL, 7, '2023-12-03 15:00:00', 0.00, 'Unpaid'),
(NULL, 8, '2023-12-04 17:00:00', 0.00, 'Unpaid'),
(NULL, 9, '2023-12-05 08:00:00', 0.00, 'Unpaid');
