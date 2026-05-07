# 🏥 Professional Hospital Management System (HMS)

A robust, enterprise-grade Hospital Management System built with **Python**, **Streamlit**, and **MySQL**. This application provides a comprehensive suite of tools for clinical, financial, and administrative operations, featuring a sophisticated role-based access control (RBAC) system and full audit logging.

---

## 🛡️ Core Roles & Capabilities

### 👑 Super Admin (System Oversight)
- **Module Switching:** Admins can toggle between HR, Doctor, Receptionist, and Accountant views without re-logging.
- **Login Tracking:** Real-time monitoring of user login frequency and timestamps.
- **Master Audit Log:** Full visibility into every system action (deletions, medical records, payments).
- **System Metrics:** Visualized statistics on user distribution and 24h activity.

### 👥 Human Resources (HR)
- **Staff Lifecycle:** Add new staff members and perform secure deletions.
- **Department Management:** Manage staff assignments and department transfers.
- **Staff Directory:** Searchable directory with role and department filtering.

### 🩺 Doctor Dashboard
- **Patient Flow:** View daily schedules with automated "Check In & Start" for arriving patients.
- **Clinical Records:** Save detailed symptoms, diagnoses, and doctor notes.
- **Seamless Prescription:** Write multi-medication prescriptions with session-locked persistence.
- **Smart Referrals:** Refer patients to other departments based on real-time doctor availability.

### 🗂️ Receptionist Dashboard
- **Smart Booking:** Appointment system that prevents doctor scheduling overlaps.
- **Patient Management:** Register new patients and manage their health profiles.
- **Today's Workflow:** Check-in patients, manage statuses, and delete erroneous appointments.
- **Bed Management:** Real-time monitoring of room and bed availability.

### 💰 Accountant Dashboard
- **Financial Processing:** Manage outpatient/inpatient invoices with automated insurance calculation.
- **Revenue Analytics:** Monthly and daily revenue visualization.
- **Currency Support:** Professional billing formatted in USD ($).

---

## 📂 Project Structure
```text
HOSPITAL-MANAGEMENT-SYSTEM/
|-- app.py              # Application entry point & routing
|-- config.py           # Database connection configuration
|-- backup.py           # Automated database backup utility
|-- requirements.txt    # Python dependency list
|-- README.md           # Project documentation
|-- .gitignore          # Git exclusion rules
|-- database_backups/   # Directory for stored SQL backups
|-- modules/            # Role-specific UI modules
|   |-- receptionist.py
|   |-- doctor.py
|   |-- accountant.py
|   |-- hr.py
|   |-- admin.py
|-- sql/                # Database scripts
|   |-- 01_create_tables.sql
|   |-- 02_logic.sql
|   |-- 03_seed_data_sql.sql
```

---

## 🛠️ Technology Stack
- **Frontend/Logic:** [Streamlit](https://streamlit.io/) & Python 3.10+
- **Database:** MySQL 8.0+ (Stored Procedures, Triggers, Views)
- **Data Engineering:** Pandas & NumPy
- **Security:** SHA-256 Hashing & Session-based Audit Attribution

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.10+
- MySQL Server

### 2. Database Initialization
1. Create a database named `hospital_db`.
2. Execute the scripts in the `sql/` directory in order:
   - `01_create_tables.sql` (Schema definition)
   - `02_logic.sql` (Business logic, triggers, and RBAC)
   - `03_seed_data_sql.sql` (Demo data population)
3. Update `config.py` with your MySQL credentials.

### 3. App Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### 4. Database Backup & Maintenance
The system includes an automated backup utility to ensure data persistence:
```bash
# Run the automated backup script
python backup.py
```
This script will:
- Attempt to use `mysqldump` for a professional-grade export.
- Fallback to a **Pure Python** implementation if system dependencies are missing.
- Save timestamped `.sql` files to the `database_backups/` directory.

---

## 🔑 Demo Credentials

| Role | Username | Password | Notes |
|------|----------|----------|-------|
| **Admin** | `admin_super` | `super_secure_hash_123` | Can switch to any role |
| **HR** | `hr_alima` | `hr123` | Managed staff and depts |
| **Doctor** | `dr_james_wilson` | `hash123` | Practice clinic workflow |
| **Receptionist** | `recep_alice` | `hash123` | Book and manage visits |
| **Accountant** | `acc_bob` | `hash123` | Financial & insurance ops |

### 🛠️ How to Remove Demo Credentials
For production or clean evaluation, you can hide the demo credentials expander from the login page:
1. Open `app.py`.
2. Locate the section labeled `# Demo credentials`.
3. Comment out or delete the code block starting from `with st.expander("🔑 Demo Credentials"):` (approx. lines 150-160).


---

## 📝 Project Status
**Status:** Stable / Professionalized

**Key Updates:** Enhanced RBAC, Multi-Prescription Session Locking, Delete Operations with Audit Trail, Master Login Tracking.