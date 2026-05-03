import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from config import get_connection

# Status display helpers
STATUS_ICON  = {
    "Scheduled": "🟡", "CheckedIn": "🔵",
    "In-Progress": "🟠", "Completed": "🟢", "Cancelled": "🔴"
}
STATUS_LABEL = {
    "Scheduled": "Scheduled", "CheckedIn": "Checked In",
    "In-Progress": "In Progress", "Completed": "Completed", "Cancelled": "Cancelled"
}


def _set_appt_status(appt_id: int, status: str):
    """Update the status of a single appointment record."""
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE appointments SET status = %s WHERE appt_id = %s",
            (status, appt_id)
        )
        conn.commit(); cur.close(); conn.close()


def _delete_appointment_ui(appt_id: int, patient_name: str):
    """Internal helper to call deletion procedure with session state check."""
    executor_id = st.session_state.get("user_id")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.callproc("sp_delete_appointment", [appt_id, executor_id])
        conn.commit(); cur.close(); conn.close()
        st.success(f"Appointment for {patient_name} deleted.")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to delete: {e}")


def _register_patient_form():
    """Inline form to create a new patient record and basic health profile."""
    with st.form("form_new_patient", clear_on_submit=True):
        st.markdown("#### Register New Patient")
        c1, c2 = st.columns(2)
        name   = c1.text_input("Full Name *")
        dob    = c2.date_input("Date of Birth", min_value=date(1900, 1, 1), max_value=date.today())
        c3, c4 = st.columns(2)
        gender = c3.selectbox("Gender", ["Male", "Female"])
        phone  = c4.text_input("Phone Number *")
        email  = st.text_input("Email Address *")

        st.markdown("**Basic Health Profile**")
        c5, c6, c7 = st.columns(3)
        blood_type = c5.selectbox("Blood Type",
                                  ["O+","O-","A+","A-","B+","B-","AB+","AB-"])
        allergies  = c6.text_input("Allergies (write 'None' if none)")
        chronic    = c7.text_input("Chronic Diseases (write 'None' if none)")

        st.markdown("**Health Insurance (Optional)**")
        c8, c9, c10 = st.columns(3)
        ins_provider = c8.text_input("Insurance Provider (Leave blank if none)")
        ins_rate = c9.number_input("Coverage Rate (%)", min_value=0, max_value=100, value=0)
        ins_expiry = c10.date_input("Expiry Date", min_value=date.today())

        if st.form_submit_button("✅ Register Patient"):
            if not all([name, phone, email]):
                st.error("Please fill in all required fields (*).")
                return
            try:
                conn = get_connection()
                cur  = conn.cursor()
                # Set session variable for audit log
                executor_id = st.session_state.get("user_id")
                if executor_id:
                    cur.execute("SET @current_user_id = %s", (executor_id,))
                cur.callproc("sp_register_patient",
                             [name, str(dob), gender, phone, email])
                conn.commit()
                cur.execute("SELECT patient_id FROM patients WHERE email = %s", (email,))
                pid = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO patient_health_profile (patient_id, blood_type, allergies, chronic_diseases)"
                    " VALUES (%s, %s, %s, %s)",
                    (pid, blood_type, allergies, chronic)
                )
                if ins_provider:
                    ins_id = f"INS-{datetime.now().year}-{pid:04d}"
                    cur.execute(
                        "INSERT INTO insurance (insurance_id, patient_id, coverage_rate, expiry_date, provider) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (ins_id, pid, ins_rate / 100.0, ins_expiry, ins_provider)
                    )
                conn.commit()
                cur.close(); conn.close()
                st.success(f"Patient **{name}** registered successfully (Patient ID: {pid}).")
            except Exception as e:
                st.error(f"Registration failed: {e}")


def _smart_booking_tab():
    """
    Smart appointment scheduling:
    1. Pick desired date/time.
    2. Query doctors whose last appointment is Completed AND who have no
       appointment within 30 minutes of the desired slot.
    3. Sort by proximity to desired time (closest available first).
    4. Confirm booking → triggers auto-invoice creation.
    """
    st.subheader("📅 Book New Appointment")

    # Step 1 — select desired date and time
    st.markdown("**Step 1 — Select desired appointment time**")
    c1, c2 = st.columns(2)
    desired_date = c1.date_input("Date", value=datetime.today())
    desired_time = c2.time_input(
        "Time",
        value=datetime.now().replace(second=0, microsecond=0).time()
    )
    desired_dt = datetime.combine(desired_date, desired_time)

    if st.button("🔍 Find Available Doctors"):
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return
        cur = conn.cursor(dictionary=True)
        # Find doctors with at least one Completed appointment
        # who are free (no appointment) for 30 min around the desired slot
        cur.execute("""
            SELECT d.doctor_id, s.full_name AS doctor_name,
                   d.specialty, dept.dept_name,
                   MAX(a.completed_at) AS last_free_at
            FROM doctors d
            JOIN staff s          ON d.staff_id  = s.staff_id
            JOIN departments dept ON s.dept_id   = dept.dept_id
            LEFT JOIN appointments a
                ON d.doctor_id = a.doctor_id AND a.status = 'Completed'
            WHERE d.doctor_id NOT IN (
                  SELECT DISTINCT doctor_id FROM appointments
                  WHERE status IN ('Scheduled','CheckedIn','In-Progress')
                    AND appt_date > DATE_SUB(%s, INTERVAL 30 MINUTE)
                    AND appt_date < DATE_ADD(%s, INTERVAL 30 MINUTE)
              )
            GROUP BY d.doctor_id, s.full_name, d.specialty, dept.dept_name
            ORDER BY IFNULL(ABS(TIMESTAMPDIFF(MINUTE, MAX(a.completed_at), %s)), 0) ASC
        """, (desired_dt, desired_dt, desired_dt))
        st.session_state["available_doctors"] = cur.fetchall()
        cur.close(); conn.close()

    # Step 2 — select a doctor from results
    if "available_doctors" in st.session_state:
        available = st.session_state["available_doctors"]
        if not available:
            st.warning("No doctors available at that time. Please try a different slot.")
            return

        st.markdown("**Step 2 — Select a doctor** _(sorted by soonest availability)_")
        doc_opts = {
            f"🩺 {d['doctor_name']} — {d['specialty']} ({d['dept_name']})": d
            for d in available
        }
        chosen_label = st.radio("Available doctors:", list(doc_opts.keys()))
        chosen_doc   = doc_opts[chosen_label]

        # Step 3 — booking form
        st.markdown("**Step 3 — Select patient**")
        with st.form("form_booking"):
            st.info(f"**Doctor:** {chosen_doc['doctor_name']} — {chosen_doc['specialty']}")
            conn2 = get_connection()
            patients = []
            if conn2:
                cur2 = conn2.cursor(dictionary=True)
                cur2.execute(
                    "SELECT patient_id, full_name, phone FROM patients ORDER BY full_name"
                )
                patients = cur2.fetchall()
                cur2.close(); conn2.close()

            pat_opts = {
                f"{p['full_name']} ({p['phone']})": p["patient_id"]
                for p in patients
            }
            chosen_pat_label = st.selectbox("Patient:", list(pat_opts.keys()))
            chosen_pat_id    = pat_opts[chosen_pat_label]
            st.caption(f"Appointment time: {desired_dt.strftime('%d/%m/%Y %H:%M')}")

            if st.form_submit_button("📋 Confirm Booking"):
                try:
                    conn3 = get_connection()
                    cur3  = conn3.cursor()
                    # Set MySQL session variable so the trigger trg_audit_appointment_creation knows who did this
                    executor_id = st.session_state.get("user_id")
                    if executor_id:
                        cur3.execute("SET @current_user_id = %s", (executor_id,))
                        
                    cur3.execute(
                        "INSERT INTO appointments"
                        " (patient_id, doctor_id, appt_date, status)"
                        " VALUES (%s, %s, %s, 'Scheduled')",
                        (chosen_pat_id, chosen_doc["doctor_id"], desired_dt)
                    )
                    conn3.commit()
                    new_id = cur3.lastrowid
                    cur3.close(); conn3.close()
                    st.success(
                        f"✅ Appointment booked for **{chosen_pat_label}** "
                        f"with **{chosen_doc['doctor_name']}** "
                        f"at {desired_dt.strftime('%H:%M %d/%m/%Y')} "
                        f"(Appointment ID: {new_id}). "
                        f"An invoice has been automatically created."
                    )
                    del st.session_state["available_doctors"]
                except Exception as e:
                    st.error(f"Booking failed: {e}")


# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────
def run():
    st.title("🗂️ Receptionist Dashboard")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Search & Check-In",
        "➕ Register Patient",
        "📅 Today's Appointments",
        "🗓️ Book New Appointment",
        "🛏️ Hospital Beds"
    ])

    # ── TAB 1: PATIENT SEARCH & CHECK-IN ─────────────────────────────────────
    with tab1:
        st.subheader("Patient Search & Check-In")
        keyword = st.text_input("🔍 Search by name or phone number:")

        if keyword:
            conn = get_connection()
            if not conn:
                st.error("Cannot connect to the database."); return
            cur = conn.cursor(dictionary=True)
            cur.callproc("sp_search_patient", [keyword])
            results = []
            for rs in cur.stored_results():
                results = rs.fetchall()
            cur.close(); conn.close()

            if results:
                st.success(f"Found **{len(results)}** patient(s).")
                for p in results:
                    with st.expander(f"👤 {p['full_name']} — {p['phone']}"):
                        c1, c2 = st.columns(2)
                        c1.write(f"**Patient ID:** {p['patient_id']}")
                        c1.write(f"**Date of Birth:** {p['dob']}")
                        c2.write(f"**Gender:** {p['gender']}")
                        c2.write(f"**Email:** {p['email']}")

                        # Show today's appointments for this patient
                        conn2 = get_connection()
                        if conn2:
                            cur2 = conn2.cursor(dictionary=True)
                            cur2.execute("""
                                SELECT a.appt_id, s.full_name AS doctor_name,
                                       doc.specialty, a.appt_date, a.status
                                FROM appointments a
                                JOIN doctors doc ON a.doctor_id = doc.doctor_id
                                JOIN staff s     ON doc.staff_id = s.staff_id
                                WHERE a.patient_id = %s
                                  AND DATE(a.appt_date) = CURDATE()
                                ORDER BY a.appt_date
                            """, (p["patient_id"],))
                            appts = cur2.fetchall()
                            cur2.close(); conn2.close()

                            if appts:
                                st.markdown("**Today's Appointments:**")
                                for a in appts:
                                    icon  = STATUS_ICON.get(a["status"], "⚪")
                                    label = STATUS_LABEL.get(a["status"], a["status"])
                                    r1, r2, r3 = st.columns([3, 2, 2])
                                    r1.write(
                                        f"**{a['doctor_name']}** ({a['specialty']}) "
                                        f"— {a['appt_date'].strftime('%H:%M')}"
                                    )
                                    r2.write(f"{icon} {label}")
                                    if a["status"] == "Scheduled":
                                        if r3.button("✅ Check In",
                                                     key=f"ci_{a['appt_id']}"):
                                            _set_appt_status(a["appt_id"], "CheckedIn")
                                            st.rerun()
                                    elif a["status"] == "CheckedIn":
                                        if r3.button("🔄 In Progress",
                                                     key=f"ip_{a['appt_id']}"):
                                            _set_appt_status(a["appt_id"], "In-Progress")
                                            st.rerun()
                            else:
                                st.info("This patient has no appointments today.")
            else:
                st.warning("No patient found with that name or phone number.")
        else:
            st.info("Enter a name or phone number to search for a patient.")

    # ── TAB 2: REGISTER NEW PATIENT ───────────────────────────────────────────
    with tab2:
        st.subheader("Register New Patient")
        st.info("Use this form to register a patient who has never visited the hospital before.")
        _register_patient_form()

    # ── TAB 3: TODAY'S APPOINTMENTS ───────────────────────────────────────────
    with tab3:
        st.subheader("Today's Appointments")
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return
        cur = conn.cursor(dictionary=True)
        # Use the SQL view specifically designed for Receptionist
        cur.execute("""
            SELECT appt_id, patient_name, patient_phone AS phone,
                   doctor_name, appt_date, appt_status AS status
            FROM view_receptionist_appointments
            WHERE DATE(appt_date) = CURDATE()
        """)
        appts = cur.fetchall()
        cur.close(); conn.close()

        if appts:
            status_filter = st.selectbox(
                "Filter by status:",
                ["All"] + list(STATUS_LABEL.keys())
            )
            filtered = (
                appts if status_filter == "All"
                else [a for a in appts if a["status"] == status_filter]
            )
            for a in filtered:
                icon  = STATUS_ICON.get(a["status"], "⚪")
                label = STATUS_LABEL.get(a["status"], a["status"])
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.write(f"**{a['patient_name']}** ({a['phone']})")
                c2.write(f"🩺 {a['doctor_name']}")
                c3.write(f"🕐 {a['appt_date'].strftime('%H:%M')}  {icon} {label}")
                if a["status"] == "Scheduled":
                    c1b, c2b = c4.columns(2)
                    if c1b.button("Check In", key=f"t2ci_{a['appt_id']}"):
                        _set_appt_status(a["appt_id"], "CheckedIn")
                        st.rerun()
                    if c2b.button("🗑️", key=f"t2del_{a['appt_id']}", help="Delete Appointment"):
                        _delete_appointment_ui(a["appt_id"], a["patient_name"])
                elif a["status"] == "CheckedIn":
                    c1b, c2b = c4.columns(2)
                    if c1b.button("In Progress", key=f"t2ip_{a['appt_id']}"):
                        _set_appt_status(a["appt_id"], "In-Progress")
                        st.rerun()
                    if c2b.button("🗑️", key=f"t2del_{a['appt_id']}", help="Delete Appointment"):
                        _delete_appointment_ui(a["appt_id"], a["patient_name"])
            st.caption(f"Total: {len(filtered)} appointment(s) shown.")
        else:
            st.info("No appointments scheduled for today.")

    # ── TAB 4: SMART BOOKING ──────────────────────────────────────────────────
    with tab4:
        _smart_booking_tab()

    # ── TAB 5: HOSPITAL BEDS ──────────────────────────────────────────────────
    with tab5:
        st.subheader("Hospital Bed Status")
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return
        cur = conn.cursor(dictionary=True)
        # Use the view designed for Room Manager/Bed Management
        cur.execute("SELECT * FROM view_hospital_bed_status ORDER BY dept_name, room_name, bed_code")
        beds = cur.fetchall()
        cur.close(); conn.close()

        if beds:
            df = pd.DataFrame(beds)
            df.columns = ["Bed Code", "Room", "Department", "Status", "Current Patient"]
            
            c1, c2 = st.columns(2)
            dept_filter = c1.selectbox("Filter by Department:", ["All"] + list(df["Department"].unique()))
            status_filter = c2.selectbox("Filter by Status:", ["All"] + list(df["Status"].unique()))
            
            if dept_filter != "All":
                df = df[df["Department"] == dept_filter]
            if status_filter != "All":
                df = df[df["Status"] == status_filter]
                
            # Color-code status: Available = Green, Occupied = Red, Maintenance = Orange
            def style_status(val):
                color = 'green' if val == 'Available' else 'red' if val == 'Occupied' else 'orange'
                return f'color: {color}; font-weight: bold'
                
            st.dataframe(df.style.map(style_status, subset=['Status']), use_container_width=True, hide_index=True)
            
            avail_count = len(df[df["Status"] == "Available"])
            st.caption(f"Showing {len(df)} beds ({avail_count} available based on current filters).")
        else:
            st.info("No beds found in the system.")
