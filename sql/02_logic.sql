-- =============================================================================
-- SCRIPT: 02_logic.sql
-- Database Target: hospital_db
-- =============================================================================

USE hospital_db;

-- =============================================================================
-- INDEXES CONFIGURATION
-- =============================================================================

-- 1. FOREIGN KEY INDEXES 
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor  ON appointments(doctor_id);

CREATE INDEX idx_admissions_patient   ON admissions(patient_id);
CREATE INDEX idx_admissions_doctor    ON admissions(doctor_id);
CREATE INDEX idx_admissions_bed       ON admissions(bed_id);

CREATE INDEX idx_medrecords_appt      ON medical_records(appt_id);
CREATE INDEX idx_medrecords_admission ON medical_records(admission_id);

CREATE INDEX idx_prescriptions_record ON prescriptions(record_id);
CREATE INDEX idx_prescriptions_doctor ON prescriptions(doctor_id);

CREATE INDEX idx_prescdetails_presc   ON presc_details(presc_id);

-- 2. COMPOSITE INDEXES 
CREATE INDEX idx_doctor_schedule      ON appointments(doctor_id, appt_date);
CREATE INDEX idx_bed_status           ON beds(room_id, status); 
CREATE INDEX idx_medicine_stock       ON medicines(category_id, med_name); 

-- 3. UNIQUE INDEXES 
CREATE UNIQUE INDEX idx_unique_staff_email ON staff(email);
-- CREATE UNIQUE INDEX idx_unique_patient_email ON patients(email);
-- CREATE UNIQUE INDEX idx_unique_patient_phone ON patients(phone);

-- 4. COVERING INDEXES 
CREATE INDEX idx_patient_lookup ON patients(full_name, patient_id);
CREATE INDEX idx_staff_login    ON staff(email, staff_id);
CREATE INDEX idx_invoice_date_status ON invoices(invoice_date, payment_status);

-- =============================================================================
-- FUNCTION
-- =============================================================================

DELIMITER //
CREATE FUNCTION fn_calculate_total_amount(p_presc_id INT) 
RETURNS DECIMAL(15,2) 
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_total DECIMAL(15,2);
    
    SELECT SUM(m.price * pd.quantity) INTO v_total
    FROM presc_details pd
    JOIN medicines m ON pd.med_id = m.med_id
    WHERE pd.presc_id = p_presc_id;
    
    RETURN IFNULL(v_total, 0);
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION fn_calculate_net_pay(p_total_amount DECIMAL(15,2), p_rate DECIMAL(3,2)) 
RETURNS DECIMAL(15,2) 
DETERMINISTIC
BEGIN
    IF p_rate IS NULL THEN RETURN p_total_amount;
    ELSE RETURN p_total_amount * (1 - p_rate);
    END IF;
END //
DELIMITER ;

-- =============================================================================
-- VIEWS (ROLE-BASED ACCESS CONTROL)
-- =============================================================================

-- 1. VIEW FOR RECEPTORS
CREATE OR REPLACE VIEW view_receptionist_appointments AS
SELECT 
    a.appt_id,
    p.full_name AS patient_name,
    p.phone AS patient_phone,
    s.full_name AS doctor_name,
    a.appt_date,
    a.status AS appt_status
FROM appointments a
JOIN patients p ON a.patient_id = p.patient_id
JOIN staff s ON a.doctor_id = s.staff_id
ORDER BY a.appt_date ASC;

-- 2. VIEW FOR DOCTORS
CREATE OR REPLACE VIEW view_doctor_work_schedule AS
SELECT 
    a.appt_id,
    s.full_name AS doctor_name,
    d.specialty, 
    DATE(a.appt_date) AS schedule_date,
    TIME(a.appt_date) AS schedule_time,
    p.full_name AS patient_name,
    ADDTIME(TIME(a.appt_date), '00:30:00') AS end_time,
    CASE 
        WHEN a.status = 'Completed' THEN 'Examined'
        WHEN a.status = 'Scheduled' THEN 'Confirmed'
        WHEN a.status = 'Cancelled' THEN 'Cancelled'
        ELSE 'Pending'
    END AS display_status
FROM appointments a
JOIN doctors d ON a.doctor_id = d.doctor_id
JOIN staff s ON d.staff_id = s.staff_id
JOIN patients p ON a.patient_id = p.patient_id
WHERE a.appt_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) 
ORDER BY a.appt_date ASC;

-- 3. VIEW FOR ROOM MANAGER
CREATE OR REPLACE VIEW view_hospital_bed_status AS
SELECT 
    b.bed_code,
    r.room_name,
    d.dept_name,
    b.status AS bed_status,
    COALESCE(p.full_name, 'Empty') AS current_patient
FROM beds b
JOIN rooms r ON b.room_id = r.room_id
JOIN departments d ON r.dept_id = d.dept_id
LEFT JOIN admissions adm ON b.bed_id = adm.bed_id AND adm.discharge_date IS NULL
LEFT JOIN patients p ON adm.patient_id = p.patient_id;

-- 4. VIEW FOR ACCOUNTANT
CREATE OR REPLACE VIEW view_detailed_patient_bill AS
SELECT
    i.invoice_id,
    i.invoice_date,
    p.full_name AS patient_name,
    mr.diagnosis AS doctor_diagnosis,
    m.med_name AS medicine_name,
    pd.dosage,
    i.total_amount AS gross_amount,
    IFNULL(ins.coverage_rate, 0) AS insurance_rate,
    fn_calculate_net_pay(i.total_amount, IFNULL(ins.coverage_rate, 0)) AS net_pay
FROM invoices i
JOIN appointments appt ON i.appt_id = appt.appt_id
JOIN patients p ON appt.patient_id = p.patient_id
LEFT JOIN insurance ins ON p.patient_id = ins.patient_id
JOIN medical_records mr ON i.appt_id = mr.appt_id
JOIN prescriptions pr ON mr.record_id = pr.record_id
JOIN presc_details pd ON pr.presc_id = pd.presc_id
JOIN medicines m ON pd.med_id = m.med_id
WHERE i.payment_status = 'Paid';

-- 5. VIEW FOR HUMAN RESOURCES
CREATE OR REPLACE VIEW view_hr_staff_directory AS
SELECT 
    s.staff_id,
    s.full_name,
    r.role_name,
    d.dept_name,
    s.phone_number,
    s.email
FROM staff s
JOIN departments d ON s.dept_id = d.dept_id
JOIN users u ON s.user_id = u.user_id
JOIN roles r ON u.role_id = r.role_id;

-- =============================================================================
-- STORED PROCEDURES
-- =============================================================================

DELIMITER //

-- 1. PATIENT MANAGEMENT
CREATE PROCEDURE sp_register_patient(IN p_full_name VARCHAR(100), IN p_dob DATE, IN p_gender VARCHAR(10), IN p_phone VARCHAR(15), IN p_email VARCHAR(100))
BEGIN
    INSERT INTO patients (full_name, dob, gender, phone, email) VALUES (p_full_name, p_dob, p_gender, p_phone, p_email);
END //

CREATE PROCEDURE sp_search_patient(IN p_keyword VARCHAR(100))
BEGIN
    SELECT * FROM patients WHERE full_name LIKE CONCAT('%', p_keyword, '%') OR phone LIKE CONCAT('%', p_keyword, '%');
END //

-- 2. CLINICAL & TREATMENT
CREATE PROCEDURE sp_create_prescription(IN p_record_id INT, IN p_patient_id INT, IN p_doctor_id INT, IN p_appointment_id INT, IN p_admission_id INT, OUT p_presc_id INT)
BEGIN
    INSERT INTO prescriptions (record_id, doctor_id) VALUES (p_record_id, p_doctor_id);
    SET p_presc_id = LAST_INSERT_ID();
END //

CREATE PROCEDURE sp_add_medicine_to_prescription(IN p_presc_id INT, IN p_med_id INT, IN p_quantity INT, IN p_dosage VARCHAR(255))
BEGIN
    INSERT INTO presc_details (presc_id, med_id, quantity, dosage) VALUES (p_presc_id, p_med_id, p_quantity, p_dosage);
END //

CREATE PROCEDURE sp_get_patient_history(IN p_patient_id INT)
BEGIN
    SELECT 'Profile' AS data_type, allergies, chronic_diseases, blood_type FROM patient_health_profile WHERE patient_id = p_patient_id;
    SELECT m.record_id, m.diagnosis, m.symptoms, m.doctor_notes, a.appt_date FROM medical_records m LEFT JOIN appointments a ON m.appt_id = a.appt_id WHERE a.patient_id = p_patient_id ORDER BY a.appt_date DESC;
END //

-- 3. SCHEDULING & ADMISSION
CREATE PROCEDURE sp_find_available_doctors(IN p_date DATE)
BEGIN
    SELECT s.staff_id, s.full_name, d.dept_name FROM staff s JOIN departments d ON s.dept_id = d.dept_id 
    WHERE s.staff_id NOT IN (SELECT DISTINCT doctor_id FROM appointments WHERE DATE(appt_date) = p_date);
END //

CREATE PROCEDURE sp_get_doctor_schedule_flow(IN p_doctor_id INT)
BEGIN
    SELECT 'Active' AS flow_type, p.full_name, a.appt_date FROM appointments a JOIN patients p ON a.patient_id = p.patient_id
    WHERE a.doctor_id = p_doctor_id AND a.status IN ('CheckedIn', 'In-Progress') AND a.appt_date <= NOW() AND DATE_ADD(a.appt_date, INTERVAL 30 MINUTE) >= NOW()
    UNION ALL
    SELECT 'Next' AS flow_type, p.full_name, a.appt_date FROM appointments a JOIN patients p ON a.patient_id = p.patient_id
    WHERE a.doctor_id = p_doctor_id AND a.status IN ('Scheduled', 'CheckedIn') AND a.appt_date > NOW() ORDER BY appt_date ASC LIMIT 1;
END //

CREATE PROCEDURE sp_discharge_patient(IN p_admission_id INT, IN p_status VARCHAR(20))
BEGIN
    UPDATE admissions SET discharge_date = NOW(), discharge_status_id = p_status WHERE admission_id = p_admission_id;
END //

-- 4. FINANCE (With RBAC)
CREATE PROCEDURE sp_pay_invoice(IN p_invoice_id INT, IN p_executor_id INT)
BEGIN
    DECLARE v_role_name VARCHAR(50);
    SELECT r.role_name INTO v_role_name FROM users u JOIN roles r ON u.role_id = r.role_id WHERE u.user_id = p_executor_id;
    IF v_role_name = 'Accountant' THEN
        UPDATE invoices SET payment_status = 'Paid' WHERE invoice_id = p_invoice_id;
    ELSE
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Permission Denied: Only Accountants';
    END IF;
END //

CREATE PROCEDURE sp_get_monthly_revenue(IN p_month INT, IN p_year INT, IN p_executor_id INT)
BEGIN
    DECLARE v_role_name VARCHAR(50);
    SELECT r.role_name INTO v_role_name FROM users u JOIN roles r ON u.role_id = r.role_id WHERE u.user_id = p_executor_id;
    IF v_role_name IN ('Accountant', 'Admin') THEN
        SELECT SUM(total_amount) AS total_revenue, COUNT(invoice_id) AS total_invoices FROM invoices WHERE MONTH(invoice_date) = p_month AND YEAR(invoice_date) = p_year AND payment_status = 'Paid';
    ELSE
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Permission Denied';
    END IF;
END //

-- 5. HR (With RBAC)
CREATE PROCEDURE sp_add_new_staff(IN p_full_name VARCHAR(100), IN p_dob DATE, IN p_gender VARCHAR(10), IN p_phone VARCHAR(15), IN p_email VARCHAR(100), IN p_user_id INT, IN p_dept_id INT, IN p_executor_id INT)
BEGIN
    DECLARE v_role_name VARCHAR(50);
    SELECT r.role_name INTO v_role_name FROM users u JOIN roles r ON u.role_id = r.role_id WHERE u.user_id = p_executor_id;
    IF v_role_name = 'HR' THEN
        INSERT INTO staff (full_name, dob, gender, phone_number, email, user_id, dept_id) VALUES (p_full_name, p_dob, p_gender, p_phone, p_email, p_user_id, p_dept_id);
    ELSE
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Permission Denied: Only HR';
    END IF;
END //

CREATE PROCEDURE sp_get_staff_by_department(IN p_dept_id INT)
BEGIN
    SELECT s.staff_id, s.full_name, s.phone_number, d.dept_name FROM staff s JOIN departments d ON s.dept_id = d.dept_id WHERE s.dept_id = p_dept_id;
END //

CREATE PROCEDURE sp_analyze_staff_activity(IN p_user_id INT)
BEGIN
    SELECT u.username, COUNT(a.log_id) AS total_actions, MAX(a.timestamp) AS last_activity FROM audit_logs a JOIN users u ON a.user_id = u.user_id WHERE a.user_id = p_user_id GROUP BY u.username;
END //

-- =============================================================================
-- AUTOMATION TRIGGERS
-- =============================================================================

CREATE TRIGGER trg_medical_record_automation
AFTER INSERT ON medical_records
FOR EACH ROW
BEGIN
    -- Kiểm tra nếu bệnh án này gắn với một cuộc hẹn (appt_id)
    IF NEW.appt_id IS NOT NULL THEN
        UPDATE appointments 
        SET status = 'Completed', 
            completed_at = NOW() -- Update completed time and status at the same time
        WHERE appt_id = NEW.appt_id;
    END IF;

END //

CREATE TRIGGER trg_release_bed_after_payment
AFTER UPDATE ON invoices
FOR EACH ROW
BEGIN
	-- 1. Check if the status changes to 'Paid' 
	-- and this bill must belong to a hospital admission case (admission_id is not NULL)
    IF NEW.payment_status = 'Paid' AND NEW.admission_id IS NOT NULL THEN
        
        -- 2. Update the bed status to Available
        UPDATE beds 
        SET status = 'Available' 
        WHERE bed_id = (SELECT bed_id FROM admissions WHERE admission_id = NEW.admission_id);
        
        -- 3. (Optional) Update always updates the library status and publication date
        UPDATE admissions 
        SET status = 'Discharged', 
            discharge_date = NOW() 
        WHERE admission_id = NEW.admission_id;

    END IF;
END //

CREATE TRIGGER trg_audit_appointment_creation
AFTER INSERT ON appointments
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action, timestamp) VALUES (NULL, CONCAT('New appointment created for patient_id: ', NEW.patient_id), NOW());
END //

CREATE TRIGGER trg_presc_detail_insert
AFTER INSERT ON presc_details
FOR EACH ROW
BEGIN
    UPDATE invoices i
    JOIN medical_records mr ON i.appt_id = mr.appt_id
    JOIN prescriptions pr ON mr.record_id = pr.record_id
    SET i.total_amount = fn_calculate_total_amount(NEW.presc_id)
    WHERE pr.presc_id = NEW.presc_id;
END //

CREATE TRIGGER trg_presc_detail_update
AFTER UPDATE ON presc_details
FOR EACH ROW
BEGIN
    UPDATE invoices i
    JOIN medical_records mr ON i.appt_id = mr.appt_id
    JOIN prescriptions pr ON mr.record_id = pr.record_id
    SET i.total_amount = fn_calculate_total_amount(NEW.presc_id)
    WHERE pr.presc_id = NEW.presc_id;
END //

CREATE TRIGGER trg_presc_detail_delete
AFTER DELETE ON presc_details
FOR EACH ROW
BEGIN
    UPDATE invoices i
    JOIN medical_records mr ON i.appt_id = mr.appt_id
    JOIN prescriptions pr ON mr.record_id = pr.record_id
    SET i.total_amount = fn_calculate_total_amount(OLD.presc_id)
    WHERE pr.presc_id = OLD.presc_id;
END //

DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_create_invoice_on_appointment
AFTER INSERT ON appointments
FOR EACH ROW
BEGIN
    -- Whenever the receptionist registers a consultation session, a pending invoice is automatically generated
    INSERT INTO invoices (appt_id, invoice_date, total_amount, payment_status)
    VALUES (NEW.appt_id, NOW(), 0, 'Unpaid');
END //
DELIMITER ;