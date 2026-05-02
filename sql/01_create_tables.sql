/*
 * PROJECT: Hospital Management System
 * STUDENT NAME: [Nguyen Ho Ngoc Minh]
 * CLASS: [DS66B]
 * DESCRIPTION: SQL Schema for Database Course - Optimized Version
 */

-- 1. Create and Select Database
DROP DATABASE IF EXISTS hospital_db;
CREATE DATABASE hospital_db;
USE hospital_db;

-- 2. Reference Tables (Catalogues)
-- Using lookup tables ensures data consistency and easier reporting
CREATE TABLE roles (
    role_id INT PRIMARY KEY, 
    role_name VARCHAR(50)
);

CREATE TABLE departments (
    dept_id INT PRIMARY KEY, 
    dept_name VARCHAR(100)
);

CREATE TABLE medicine_categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT, 
    category_name VARCHAR(100)
);

-- 3. Core Entities
CREATE TABLE patients (
    patient_id INT PRIMARY KEY AUTO_INCREMENT, 
    full_name VARCHAR(100), 
    dob DATE, 
    gender VARCHAR(10), 
    phone VARCHAR(15), 
    email VARCHAR(100) UNIQUE
);

CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT, 
    username VARCHAR(50) UNIQUE, 
    password_hash VARCHAR(255), 
    role_id INT, 
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE TABLE medicines (
    med_id INT PRIMARY KEY, 
    med_name VARCHAR(100), 
    stock INT, 
    price DECIMAL(10,2), 
    category_id INT, 
    FOREIGN KEY (category_id) REFERENCES medicine_categories(category_id)
);

CREATE TABLE rooms (
    room_id INT PRIMARY KEY, 
    room_name VARCHAR(50), 
    dept_id INT, 
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- 4. Dependent Tables
CREATE TABLE staff (
    staff_id INT PRIMARY KEY AUTO_INCREMENT, 
    full_name VARCHAR(100), 
    dob DATE, 
    gender VARCHAR(10), 
    phone_number VARCHAR(15), 
    email VARCHAR(100) UNIQUE, 
    user_id INT, 
    dept_id INT, 
    FOREIGN KEY (user_id) REFERENCES users(user_id), 
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE beds (
    bed_id INT PRIMARY KEY, 
    bed_code VARCHAR(20), 
    room_id INT, 
    status ENUM('Available', 'Occupied', 'Cleaning', 'Maintenance') DEFAULT 'Available', 
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

CREATE TABLE insurance (
    insurance_id VARCHAR(20) PRIMARY KEY, 
    patient_id INT,
    coverage_rate DECIMAL(3,2) DEFAULT 0.00,
    expiry_date DATE, 
    provider VARCHAR(100), 
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE patient_health_profile (
    profile_id INT PRIMARY KEY AUTO_INCREMENT, 
    patient_id INT, 
    allergies TEXT, 
    chronic_diseases TEXT, 
    blood_type VARCHAR(3), 
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

-- 5. Operational Tables
CREATE TABLE doctors (
    doctor_id INT PRIMARY KEY AUTO_INCREMENT, 
    staff_id INT, 
    specialty VARCHAR(100), 
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
);

CREATE TABLE appointments (
    appt_id INT PRIMARY KEY AUTO_INCREMENT, 
    patient_id INT, 
    doctor_id INT, 
    appt_date DATETIME,
    completed_at DATETIME NULL,
    status ENUM('Scheduled', 'CheckedIn', 'In-Progress', 'Completed', 'Cancelled') DEFAULT 'Scheduled', 
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id), 
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE admissions (
    admission_id INT PRIMARY KEY AUTO_INCREMENT, 
    patient_id INT, 
    doctor_id INT, 
    bed_id INT, 
    admission_date DATETIME, 
    discharge_date DATETIME, 
    discharge_status VARCHAR(255),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id), 
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id), 
    FOREIGN KEY (bed_id) REFERENCES beds(bed_id)
);

-- 6. Clinical Records & Finance
CREATE TABLE medical_records (
    record_id INT PRIMARY KEY AUTO_INCREMENT, 
    appt_id INT NULL, 
    admission_id INT NULL, 
    symptoms TEXT, 
    diagnosis VARCHAR(255), 
    doctor_notes TEXT, 
    FOREIGN KEY (appt_id) REFERENCES appointments(appt_id), 
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);

CREATE TABLE prescriptions (
    presc_id INT PRIMARY KEY AUTO_INCREMENT, 
    record_id INT, 
    doctor_id INT, 
    FOREIGN KEY (record_id) REFERENCES medical_records(record_id), 
    FOREIGN KEY (doctor_id) REFERENCES staff(staff_id)
);

CREATE TABLE presc_details (
    detail_id INT PRIMARY KEY AUTO_INCREMENT, 
    presc_id INT, 
    med_id INT, 
    quantity INT, 
    dosage VARCHAR(255), 
    FOREIGN KEY (presc_id) REFERENCES prescriptions(presc_id), 
    FOREIGN KEY (med_id) REFERENCES medicines(med_id)
);

CREATE TABLE invoices (
    invoice_id INT PRIMARY KEY AUTO_INCREMENT, 
    appt_id INT NULL, 
    admission_id INT NULL,
    invoice_date DATETIME,
    total_amount DECIMAL(10,2), 
    payment_status VARCHAR(20), 
    FOREIGN KEY (appt_id) REFERENCES appointments(appt_id), 
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);

CREATE TABLE audit_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT, 
    user_id INT, 
    action VARCHAR(255), 
    timestamp DATETIME, 
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);