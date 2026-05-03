import streamlit as st
import pandas as pd
import hashlib
from datetime import date
from config import get_connection


def run():
    st.title("👥 Human Resources (HR)")

    # Resolve executor identity from session (Admin user)
    executor_id = st.session_state.get("user_id", 23)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Staff Directory",
        "➕ Add New Staff",
        "🩺 Doctor Credentials",
        "📊 Activity Logs"
    ])

    # ── TAB 1: STAFF DIRECTORY & DEPARTMENT TRANSFER ─────────────────────────
    with tab1:
        st.subheader("Staff Directory")
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return

        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT dept_id, dept_name FROM departments ORDER BY dept_name")
        depts = cur.fetchall()
        cur.execute("SELECT role_name FROM roles ORDER BY role_name")
        role_names = [r["role_name"] for r in cur.fetchall()]
        cur.execute("SELECT * FROM view_hr_staff_directory")
        all_staff = cur.fetchall()
        cur.close(); conn.close()

        # Filter controls
        c1, c2 = st.columns(2)
        dept_filter = c1.selectbox("Filter by Department:", ["All"] + [d["dept_name"] for d in depts])
        role_filter = c2.selectbox("Filter by Role:", ["All"] + role_names)

        staff = all_staff
        if dept_filter != "All":
            staff = [s for s in staff if s["dept_name"] == dept_filter]
        if role_filter != "All":
            staff = [s for s in staff if s["role_name"] == role_filter]

        if staff:
            df = pd.DataFrame(staff)
            df.columns = ["ID", "Full Name", "Role", "Department", "Phone", "Email"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No staff members found with the selected filters.")

        # Department transfer section
        st.markdown("---")
        st.subheader("🔄 Department Transfer")
        if all_staff:
            c3, c4 = st.columns(2)
            staff_map = {s["full_name"]: s["staff_id"] for s in all_staff}
            chosen_name  = c3.selectbox("Select staff member:", list(staff_map.keys()))
            new_dept_name = c4.selectbox("Transfer to department:", [d["dept_name"] for d in depts])
            new_dept_id   = next(d["dept_id"] for d in depts if d["dept_name"] == new_dept_name)

            if st.button("✅ Confirm Transfer"):
                try:
                    c = get_connection()
                    cu = c.cursor()
                    # Log the transfer
                    if executor_id:
                        cu.execute("SET @current_user_id = %s", (executor_id,))
                    cu.execute(
                        "UPDATE staff SET dept_id = %s WHERE staff_id = %s",
                        (new_dept_id, staff_map[chosen_name])
                    )
                    cu.execute(
                        "INSERT INTO audit_logs (user_id, action, timestamp) VALUES (%s, %s, NOW())",
                        (executor_id, f"Transferred staff {chosen_name} to {new_dept_name}")
                    )
                    c.commit(); cu.close(); c.close()
                    st.success(f"**{chosen_name}** has been transferred to **{new_dept_name}**.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Transfer failed: {e}")

        # Delete Staff section
        st.markdown("---")
        st.subheader("🗑️ Delete Staff")
        st.warning("⚠️ Warning: Deleting a staff member will also remove their doctor profile (if any). This action cannot be undone.")
        if all_staff:
            c5, c6 = st.columns([3, 1])
            staff_to_delete_name = c5.selectbox("Select staff member to REMOVE:", list(staff_map.keys()), key="delete_staff_select")
            staff_to_delete_id = staff_map[staff_to_delete_name]
            
            if c6.button("❌ DELETE", use_container_width=True):
                # Extra confirmation via session state
                st.session_state["confirm_delete_id"] = staff_to_delete_id
                st.session_state["confirm_delete_name"] = staff_to_delete_name
            
            if st.session_state.get("confirm_delete_id") == staff_to_delete_id:
                st.error(f"Are you sure you want to delete **{staff_to_delete_name}**?")
                col_y, col_n = st.columns(2)
                if col_y.button("Yes, Permanent Delete", key="btn_confirm_y"):
                    try:
                        c = get_connection()
                        cu = c.cursor()
                        cu.callproc("sp_delete_staff", [staff_to_delete_id, executor_id])
                        c.commit(); cu.close(); c.close()
                        st.success(f"Staff member **{staff_to_delete_name}** deleted.")
                        del st.session_state["confirm_delete_id"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
                if col_n.button("Cancel", key="btn_confirm_n"):
                    del st.session_state["confirm_delete_id"]
                    st.rerun()

    # ── TAB 2: ADD NEW STAFF ──────────────────────────────────────────────────
    with tab2:
        st.subheader("Add New Staff Member")
        conn2 = get_connection()
        if not conn2:
            st.error("Cannot connect to the database."); return
        cur2 = conn2.cursor(dictionary=True)
        cur2.execute("SELECT dept_id, dept_name FROM departments ORDER BY dept_name")
        depts2 = cur2.fetchall()
        cur2.execute("SELECT role_id, role_name FROM roles ORDER BY role_name")
        roles2 = cur2.fetchall()
        cur2.close(); conn2.close()

        with st.form("form_add_staff", clear_on_submit=True):
            st.markdown("**Personal Information**")
            c1, c2 = st.columns(2)
            full_name = c1.text_input("Full Name *")
            dob       = c2.date_input("Date of Birth", min_value=date(1900, 1, 1), max_value=date.today())
            c3, c4 = st.columns(2)
            gender = c3.selectbox("Gender", ["Male", "Female"])
            phone  = c4.text_input("Phone Number *")
            email  = st.text_input("Email Address *")

            st.markdown("**Assignment**")
            c5, c6 = st.columns(2)
            dept_choice = c5.selectbox("Department", [d["dept_name"] for d in depts2])
            role_choice = c6.selectbox("Role",       [r["role_name"] for r in roles2])
            dept_id = next(d["dept_id"] for d in depts2 if d["dept_name"] == dept_choice)
            role_id = next(r["role_id"] for r in roles2 if r["role_name"] == role_choice)

            st.markdown("**System Account**")
            c7, c8 = st.columns(2)
            username = c7.text_input("Username *")
            password = c8.text_input("Password *", type="password")

            # Extra field for Doctor role
            specialty = None
            if role_choice == "Doctor":
                st.markdown("**Doctor Information**")
                specialty = st.selectbox("Specialty", [
                    "Internal Medicine", "Pediatrics", "Obstetrics and Gynecology",
                    "Otolaryngology", "General Surgery", "Dermatology"
                ])

            if st.form_submit_button("➕ Add Staff Member"):
                if not all([full_name, phone, email, username, password]):
                    st.error("Please fill in all required fields (*).")
                else:
                    try:
                        c = get_connection()
                        cu = c.cursor()
                        # Hash password with SHA-256 before storing
                        pw_hash = hashlib.sha256(password.encode()).hexdigest()
                        cu.execute(
                            "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s)",
                            (username, pw_hash, role_id)
                        )
                        new_user_id = cu.lastrowid
                        # Create the staff record via stored procedure
                        cu.callproc("sp_add_new_staff", [
                            full_name, str(dob), gender, phone, email,
                            new_user_id, dept_id, executor_id
                        ])
                        c.commit()
                        # If Doctor role: also insert into doctors table
                        if role_choice == "Doctor" and specialty:
                            cu.execute(
                                "SELECT staff_id FROM staff WHERE email = %s", (email,)
                            )
                            row = cu.fetchone()
                            if row:
                                cu.execute(
                                    "INSERT INTO doctors (staff_id, specialty) VALUES (%s, %s)",
                                    (row[0], specialty)
                                )
                                c.commit()
                        cu.close(); c.close()
                        st.success(f"Staff member **{full_name}** added successfully!")
                    except Exception as e:
                        st.error(f"Error adding staff: {e}")

    # ── TAB 3: DOCTOR CREDENTIALS ─────────────────────────────────────────────
    with tab3:
        st.subheader("Doctor Credentials & Appointment Statistics")
        conn3 = get_connection()
        if not conn3:
            st.error("Cannot connect to the database."); return
        cur3 = conn3.cursor(dictionary=True)
        cur3.execute("""
            SELECT d.doctor_id, s.full_name, d.specialty, dept.dept_name,
                   s.phone_number, s.email,
                   COUNT(a.appt_id) AS total_appointments
            FROM doctors d
            JOIN staff s          ON d.staff_id  = s.staff_id
            JOIN departments dept ON s.dept_id   = dept.dept_id
            LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
            GROUP BY d.doctor_id, s.full_name, d.specialty,
                     dept.dept_name, s.phone_number, s.email
            ORDER BY dept.dept_name, s.full_name
        """)
        doctors = cur3.fetchall()
        cur3.close(); conn3.close()

        if doctors:
            df3 = pd.DataFrame(doctors)
            df3.columns = ["Doctor ID", "Full Name", "Specialty", "Department",
                           "Phone", "Email", "Total Appointments"]
            st.dataframe(df3, use_container_width=True, hide_index=True)
        else:
            st.info("No doctors found in the system.")

        st.markdown("---")
        st.info(
            "⏳ **Shift Scheduling** and **Attendance Tracking** are planned features. "
            "They require additional tables (`shifts`, `attendance`) to be added to the schema."
        )

    # ── TAB 4: ACTIVITY LOGS ──────────────────────────────────────────────────
    with tab4:
        st.subheader("Staff Activity Analysis")
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT s.full_name, u.user_id, u.username
            FROM staff s
            JOIN users u ON s.user_id = u.user_id
            ORDER BY s.full_name
        """)
        users = cur.fetchall()
        cur.close(); conn.close()

        if users:
            user_opts = {f"{u['full_name']} (@{u['username']})": u['user_id'] for u in users}
            selected_user_label = st.selectbox("Select Staff Member to Analyze:", list(user_opts.keys()))
            selected_user_id = user_opts[selected_user_label]

            if st.button("🔍 Analyze Activity"):
                conn2 = get_connection()
                if conn2:
                    cur2 = conn2.cursor(dictionary=True)
                    try:
                        cur2.callproc("sp_analyze_staff_activity", [selected_user_id])
                        stats = []
                        for rs in cur2.stored_results():
                            stats.extend(rs.fetchall())
                        
                        if stats:
                            st.success(f"Activity found for **{selected_user_label}**:")
                            c1, c2 = st.columns(2)
                            c1.metric("Total Actions Logged", stats[0]['total_actions'])
                            c2.metric("Last Activity", str(stats[0]['last_activity']))
                        else:
                            st.info("No activity logs found for this user.")
                    except Exception as e:
                        st.error(f"Error analyzing activity: {e}")
                    cur2.close(); conn2.close()
        else:
            st.info("No users found.")
