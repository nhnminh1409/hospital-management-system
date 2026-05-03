import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import get_connection

STATUS_ICON  = {
    "Scheduled": "🟡", "CheckedIn": "🔵",
    "In-Progress": "🟠", "Completed": "🟢", "Cancelled": "🔴"
}
STATUS_LABEL = {
    "Scheduled": "Scheduled", "CheckedIn": "Checked In",
    "In-Progress": "In Progress", "Completed": "Completed", "Cancelled": "Cancelled"
}


def run():
    st.title("🩺 Doctor Dashboard")

    # Resolve identity from session state (set during login)
    doctor_id = st.session_state.get("doctor_id")
    full_name  = st.session_state.get("full_name", "Doctor")

    if not doctor_id:
        st.error(
            "Your account is not linked to any doctor record. "
            "Please contact HR to set up your doctor profile."
        )
        return

    # Fetch doctor details (specialty, department)
    conn = get_connection()
    if not conn:
        st.error("Cannot connect to the database."); return
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT d.specialty, dept.dept_name
        FROM doctors d
        JOIN staff s          ON d.staff_id  = s.staff_id
        JOIN departments dept ON s.dept_id   = dept.dept_id
        WHERE d.doctor_id = %s
    """, (doctor_id,))
    me = cur.fetchone()
    cur.close(); conn.close()

    if me:
        st.markdown(
            f"### Welcome, **{full_name}** | "
            f"{me['specialty']} — {me['dept_name']}"
        )
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 My Schedule",
        "🔄 Current Flow",
        "🩺 Examine Patient",
        "📖 Patient History",
        "🔀 Refer Patient"
    ])

    # ── TAB 1: MY SCHEDULE ────────────────────────────────────────────────────
    with tab1:
        st.subheader("My Appointment Schedule (Last 7 Days)")
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return
        cur = conn.cursor(dictionary=True)
        # Use the SQL view specifically designed for Doctors
        cur.execute("""
            SELECT appt_id,
                   patient_name,
                   schedule_date AS appt_day,
                   schedule_time AS appt_time,
                   display_status AS status
            FROM view_doctor_work_schedule
            WHERE doctor_name = %s
            ORDER BY schedule_date, schedule_time
        """, (full_name,))
        schedule = cur.fetchall()
        cur.close(); conn.close()

        if schedule:
            df = pd.DataFrame(schedule)
            df["Status"] = df["status"].map(
                lambda s: f"{STATUS_ICON.get(s,'⚪')} {STATUS_LABEL.get(s,s)}"
            )
            df = df.rename(columns={
                "appt_id": "ID", "patient_name": "Patient",
                "appt_day": "Date", "appt_time": "Time"
            })
            st.dataframe(
                df[["ID", "Patient", "Date", "Time", "Status"]],
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No appointments in the last 7 days.")

    # ── TAB 2: CURRENT FLOW ───────────────────────────────────────────────────
    with tab2:
        st.subheader("Current Patient Flow")
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return
        cur = conn.cursor(dictionary=True)
        # Use stored procedure to get active and next patient
        try:
            cur.callproc("sp_get_doctor_schedule_flow", [doctor_id])
            flow_results = []
            for rs in cur.stored_results():
                flow_results.extend(rs.fetchall())
        except Exception as e:
            st.error(f"Error fetching flow: {e}")
        cur.close(); conn.close()

        if flow_results:
            for row in flow_results:
                if row['flow_type'] == 'Active':
                    st.success(f"🟢 **Currently Examining:** {row['full_name']} — {row['appt_date'].strftime('%H:%M')}")
                elif row['flow_type'] == 'Next':
                    st.info(f"⏭️ **Next Up:** {row['full_name']} — {row['appt_date'].strftime('%H:%M')}")
        else:
            st.info("No active or upcoming patients at this moment.")

    # ── TAB 3: EXAMINE PATIENT ────────────────────────────────────────────────
    with tab3:
        st.subheader("Examine Current Patient")
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return
        cur = conn.cursor(dictionary=True)
        # Fetch active appointments (CheckedIn or In-Progress) for this doctor
        cur.execute("""
            SELECT a.appt_id, p.patient_id, p.full_name AS patient_name,
                   a.appt_date, a.status,
                   php.blood_type, php.allergies, php.chronic_diseases
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            LEFT JOIN patient_health_profile php
                ON p.patient_id = php.patient_id
            WHERE a.doctor_id = %s
              AND a.status IN ('Scheduled', 'CheckedIn', 'In-Progress')
            ORDER BY a.appt_date
        """, (doctor_id,))
        active = cur.fetchall()
        cur.close(); conn.close()

        # [CẢI TIẾN] Xác định bệnh nhân đang được khám
        appt = None
        if "current_exam_appt" in st.session_state:
            appt = st.session_state["current_exam_appt"]
        elif active:
            # Allow doctor to select which patient to examine
            pat_opts = {
                f"{a['patient_name']} — {a['appt_date'].strftime('%H:%M')} "
                f"({STATUS_LABEL.get(a['status'], a['status'])})": a
                for a in active
            }
            chosen_label = st.selectbox("Select patient:", list(pat_opts.keys()))
            appt = pat_opts[chosen_label]
        
        if not appt:
            st.info("No patients currently waiting or in progress.")
            return

        # --- GIAO DIỆN KHÁM BỆNH ---
        # Health profile summary card

        # Health profile summary card
        with st.expander("📋 Health Profile", expanded=True):
            c1, c2, c3 = st.columns(3)
            c1.metric("Blood Type", appt.get("blood_type") or "—")
            c2.markdown(f"**Allergies:** {appt.get('allergies') or '—'}")
            c3.markdown(
                f"**Chronic Diseases:** {appt.get('chronic_diseases') or '—'}"
            )

        # CASE 1: Patient has just arrived (CheckedIn) or we are doing Auto-Check-In (Scheduled)
        if appt["status"] in ["Scheduled", "CheckedIn"]:
            btn_label = "▶️ Start Examination" if appt["status"] == "CheckedIn" else "✅ Check In & Start"
            if st.button(btn_label):
                conn2 = get_connection()
                if conn2:
                    cur2 = conn2.cursor()
                    cur2.execute(
                        "UPDATE appointments SET status = 'In-Progress'"
                        " WHERE appt_id = %s",
                        (appt["appt_id"],)
                    )
                    conn2.commit(); cur2.close(); conn2.close()
                
                # 'Lock' the appointment into session state immediately
                appt["status"] = "In-Progress" 
                st.session_state["current_exam_appt"] = appt
                st.rerun()

        if appt["status"] in ["In-Progress", "Completed"]:
            st.markdown("---")
            st.markdown("#### Medical Record")
            
            # Show form only if record not yet saved in this session
            if "exam_record_id" not in st.session_state:
                with st.form("form_examine"):
                    symptoms     = st.text_area("Symptoms *")
                    diagnosis    = st.text_input("Diagnosis *")
                    doctor_notes = st.text_area("Doctor Notes")
                    save_record  = st.form_submit_button("💾 Save Medical Record")

                if save_record:
                    if not symptoms or not diagnosis:
                        st.error("Please fill in symptoms and diagnosis.")
                    else:
                        try:
                            conn3 = get_connection()
                            cur3  = conn3.cursor()
                            executor_id = st.session_state.get("user_id")
                            if executor_id:
                                cur3.execute("SET @current_user_id = %s", (executor_id,))
                            cur3.execute(
                                "INSERT INTO medical_records (appt_id, symptoms, diagnosis, doctor_notes) VALUES (%s, %s, %s, %s)",
                                (appt["appt_id"], symptoms, diagnosis, doctor_notes)
                            )
                            conn3.commit()
                            
                            # LOCK the appointment now if not already locked
                            st.session_state["current_exam_appt"] = appt
                            st.session_state["exam_record_id"] = cur3.lastrowid
                            st.session_state["exam_doctor_id"] = doctor_id
                            
                            cur3.close(); conn3.close()
                            st.success("✅ Record saved. Now write a prescription.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.success(f"✅ Medical Record Saved (ID: {st.session_state['exam_record_id']})")

            # Prescription section
            if "exam_record_id" in st.session_state:
                st.markdown("---")
                st.markdown("#### 💊 Write Prescription")
                conn4 = get_connection()
                meds = []
                if conn4:
                    cur4 = conn4.cursor(dictionary=True)
                    cur4.execute("SELECT med_id, med_name, price, stock FROM medicines ORDER BY med_name")
                    meds = cur4.fetchall()
                    cur4.close(); conn4.close()

                with st.form("form_prescription", clear_on_submit=True):
                    med_opts = {f"{m['med_name']} (stock: {m['stock']}, price: ${m['price']:,.2f})": m for m in meds}
                    chosen_med_label = st.selectbox("Select Medicine:", list(med_opts.keys()))
                    chosen_med = med_opts[chosen_med_label]
                    dosage = st.text_input("Dosage")
                    quantity = st.number_input("Quantity", min_value=1, value=7)
                    add_med = st.form_submit_button("➕ Add to Prescription")

                if add_med:
                    try:
                        conn5 = get_connection()
                        cur5 = conn5.cursor()
                        if "exam_presc_id" not in st.session_state:
                            result = cur5.callproc("sp_create_prescription", [st.session_state["exam_record_id"], st.session_state["exam_doctor_id"], 0])
                            conn5.commit()
                            st.session_state["exam_presc_id"] = result[2]
                        cur5.callproc("sp_add_medicine_to_prescription", [st.session_state["exam_presc_id"], chosen_med["med_id"], int(quantity), dosage])
                        conn5.commit(); cur5.close(); conn5.close()
                        st.success(f"✅ {chosen_med['med_name']} added.")
                    except Exception as e:
                        st.error(f"Error: {e}")

                if "exam_presc_id" in st.session_state:
                    conn_disp = get_connection()
                    if conn_disp:
                        cur_disp = conn_disp.cursor(dictionary=True)
                        cur_disp.execute("SELECT m.med_name, pd.dosage, pd.quantity FROM presc_details pd JOIN medicines m ON pd.med_id = m.med_id WHERE pd.presc_id = %s", (st.session_state["exam_presc_id"],))
                        items = cur_disp.fetchall()
                        cur_disp.close(); conn_disp.close()
                        if items:
                            st.dataframe(pd.DataFrame(items), hide_index=True, use_container_width=True)

                if st.button("🏁 End Consultation Session"):
                    conn6 = get_connection()
                    if conn6:
                        cur6 = conn6.cursor()
                        cur6.execute("UPDATE appointments SET status = 'Completed', completed_at = NOW() WHERE appt_id = %s", (appt["appt_id"],))
                        conn6.commit(); cur6.close(); conn6.close()
                    for k in ["exam_record_id", "exam_presc_id", "exam_doctor_id", "current_exam_appt"]:
                        st.session_state.pop(k, None)
                    st.success("Consultation ended!")
                    st.rerun()

    # ── TAB 4: PATIENT HISTORY ────────────────────────────────────────────────
    with tab4:
        st.subheader("Patient Medical History")
        keyword = st.text_input("🔍 Search patient by name or phone:", key="doc_search")
        if keyword:
            conn = get_connection()
            if not conn:
                st.error("Cannot connect to the database."); return
            cur = conn.cursor(dictionary=True)
            cur.callproc("sp_search_patient", [keyword])
            patients = []
            for rs in cur.stored_results():
                patients = rs.fetchall()
            cur.close(); conn.close()

            if patients:
                pat_opts = {
                    f"{p['full_name']} ({p['phone']})": p["patient_id"]
                    for p in patients
                }
                chosen_label = st.selectbox("Select patient:", list(pat_opts.keys()))
                pid = pat_opts[chosen_label]

                conn2 = get_connection()
                if conn2:
                    cur2 = conn2.cursor(dictionary=True)
                    cur2.callproc("sp_get_patient_history", [pid])
                    results = [rs.fetchall() for rs in cur2.stored_results()]
                    cur2.close(); conn2.close()

                    if results and results[0]:
                        prof = results[0][0]
                        st.markdown("**Health Profile**")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Blood Type",       prof.get("blood_type", "—"))
                        c2.markdown(f"**Allergies:** {prof.get('allergies', '—')}")
                        c3.markdown(
                            f"**Chronic Diseases:** {prof.get('chronic_diseases', '—')}"
                        )
                    if len(results) > 1 and results[1]:
                        st.markdown("**Visit History**")
                        df = pd.DataFrame(results[1])
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No visit history found for this patient.")
            else:
                st.warning("No patient found with that search term.")
        else:
            st.info("Enter a patient name or phone number to search.")

    # ── TAB 5: REFER PATIENT ──────────────────────────────────────────────────
    with tab5:
        st.subheader("Refer Patient to Another Department")

        # Find today's patients for this doctor (CheckedIn, In-Progress, or Completed)
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT a.appt_id, p.patient_id, p.full_name AS patient_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            WHERE a.doctor_id = %s
              AND a.status IN ('CheckedIn','In-Progress','Completed')
              AND DATE(a.appt_date) = CURDATE()
        """, (doctor_id,))
        today_patients = cur.fetchall()
        cur.close(); conn.close()

        if not today_patients:
            st.info("No patients seen today to refer.")
        else:
            pat_opts = {p["patient_name"]: p for p in today_patients}
            chosen_pat_label = st.selectbox("Select patient to refer:",
                                            list(pat_opts.keys()))
            ref_patient = pat_opts[chosen_pat_label]

            # Find available doctors in OTHER specialties within next 30 min
            desired_dt = datetime.now() + timedelta(minutes=5)
            conn2 = get_connection()
            avail = []
            if conn2:
                cur2 = conn2.cursor(dictionary=True)
                cur2.execute("""
                    SELECT d.doctor_id, s.full_name AS doctor_name,
                           d.specialty, dept.dept_name,
                           MAX(a.completed_at) AS last_free_at
                    FROM doctors d
                    JOIN staff s          ON d.staff_id  = s.staff_id
                    JOIN departments dept ON s.dept_id   = dept.dept_id
                    LEFT JOIN appointments a
                        ON d.doctor_id = a.doctor_id AND a.status = 'Completed'
                    WHERE d.doctor_id != %s
                      AND d.doctor_id NOT IN (
                        SELECT DISTINCT doctor_id FROM appointments
                        WHERE status IN ('Scheduled','CheckedIn','In-Progress')
                          AND appt_date > DATE_SUB(%s, INTERVAL 30 MINUTE)
                          AND appt_date < DATE_ADD(%s, INTERVAL 30 MINUTE)
                    )
                    GROUP BY d.doctor_id, s.full_name, d.specialty, dept.dept_name
                    ORDER BY IFNULL(ABS(TIMESTAMPDIFF(MINUTE, MAX(a.completed_at), %s)), 0) ASC
                    LIMIT 10
                """, (doctor_id, desired_dt, desired_dt, desired_dt))
                avail = cur2.fetchall()
                cur2.close(); conn2.close()

            if not avail:
                st.warning("No other doctors are currently available for referral.")
            else:
                ref_opts = {
                    f"🩺 {d['doctor_name']} — {d['specialty']} ({d['dept_name']})": d
                    for d in avail
                }
                chosen_ref_label = st.radio("Available doctors for referral:",
                                            list(ref_opts.keys()))
                chosen_ref = ref_opts[chosen_ref_label]

                if st.button(f"📋 Confirm Referral → {chosen_ref['doctor_name']}"):
                    try:
                        conn3 = get_connection()
                        cur3  = conn3.cursor()
                        # Set MySQL session variable so the trigger trg_audit_appointment_creation knows who did this
                        # Set session variable for audit trigger (must use user_id, not doctor_id)
                        executor_id = st.session_state.get("user_id")
                        if executor_id:
                            cur3.execute("SET @current_user_id = %s", (executor_id,))
                            
                        cur3.execute(
                            "INSERT INTO appointments"
                            " (patient_id, doctor_id, appt_date, status)"
                            " VALUES (%s, %s, %s, 'Scheduled')",
                            (ref_patient["patient_id"],
                             chosen_ref["doctor_id"], desired_dt)
                        )
                        conn3.commit()
                        new_id = cur3.lastrowid
                        cur3.close(); conn3.close()
                        st.success(
                            f"✅ **{ref_patient['patient_name']}** referred to "
                            f"**{chosen_ref['doctor_name']}** ({chosen_ref['specialty']}).  \n"
                            f"New appointment ID: {new_id} — "
                            f"{desired_dt.strftime('%H:%M %d/%m/%Y')}"
                        )
                    except Exception as e:
                        st.error(f"Referral failed: {e}")
