USE hospital_db;

-- ======================================================
-- REFERENCE DATA
-- ======================================================
INSERT INTO roles (role_id, role_name) VALUES 
(1, 'Admin'), (2, 'Doctor'), (3, 'Receptionist'), (4, 'Accountant');

INSERT INTO departments (dept_id, dept_name) VALUES 
(1, 'Internal Medicine'), (2, 'Pediatrics'), (3, 'Obstetrics and Gynecology'), 
(4, 'Otolaryngology'), (5, 'General Surgery'), (6, 'Dermatology'), (7, 'Administration');

-- ======================================================
-- 3. USERS (22 Accounts)
-- ======================================================
INSERT INTO users (user_id, username, password_hash, role_id) VALUES 
(1, 'recep_alice', 'hash123', 3),
(2, 'acc_bob', 'hash123', 4),
(23, 'admin_super', 'super_secure_hash_123', 1);

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
(23, 'Justin Bieber', '1990-07-24', 'Male', '0823468445', 'justin.b@hosp.com',23,7);

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

-- ======================================================
-- 7. PATIENT HEALTH PROFILES (20 Profiles)
-- ======================================================
INSERT INTO patient_health_profile (profile_id, patient_id, allergies, chronic_diseases, blood_type)
SELECT patient_id, patient_id, 'None', 'None', 'O+' FROM patients;

-- ======================================================
-- 8. DEMO APPOINTMENTS
-- ======================================================
INSERT INTO appointments (appt_id, patient_id, doctor_id, appt_date, status) VALUES 
(1, 1, 1, '2026-04-30 08:30:00', 'Completed'),
(2, 2, 4, '2026-04-30 09:15:00', 'Scheduled'),
(3, 3, 8, '2026-05-01 10:00:00', 'Scheduled');