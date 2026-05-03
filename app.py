import streamlit as st
import hashlib
from config import get_connection

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hospital Management System",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2044 0%, #1a3a6b 100%);
}
[data-testid="stSidebar"] * { color: #e8f0fe !important; }
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.3);
    color: white !important;
}
/* Login card */
.login-card {
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 8px 32px rgba(15,32,68,0.15);
}
/* Metric cards */
div[data-testid="metric-container"] {
    background: #f0f4ff;
    border-radius: 10px;
    padding: 1rem;
    border-left: 4px solid #4a6cf7;
}
</style>
""", unsafe_allow_html=True)


# ── AUTHENTICATION ────────────────────────────────────────────────────────────
def authenticate(username: str, password: str) -> dict | None:
    """
    Verify credentials against the database.
    Supports both SHA-256 hashed passwords (new accounts via HR)
    and plain-text password_hash values (seed data).
    """
    conn = get_connection()
    if not conn:
        return None
    cur = conn.cursor(dictionary=True)
    sha256_pw = hashlib.sha256(password.encode()).hexdigest()
    cur.execute("""
        SELECT u.user_id, u.username, r.role_name,
               s.full_name, s.staff_id
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        LEFT JOIN staff s ON u.user_id = s.user_id
        WHERE u.username = %s
          AND (u.password_hash = %s OR u.password_hash = %s)
    """, (username, sha256_pw, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


def _load_doctor_id(staff_id: int) -> int | None:
    """Fetch doctor_id for a given staff_id (Doctor role only)."""
    conn = get_connection()
    if not conn:
        return None
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT doctor_id FROM doctors WHERE staff_id = %s", (staff_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["doctor_id"] if row else None


def logout():
    """Clear all session state to force redirect to login page."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# ── LOGIN PAGE ────────────────────────────────────────────────────────────────
def show_login_page():
    """Render the centered login form."""
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("""
        <div style="text-align:center; padding:2rem 0 1.5rem 0;">
            <div style="font-size:4rem;">🏥</div>
            <h1 style="color:#0f2044; margin:0; font-size:1.8rem;">
                Hospital Management System
            </h1>
            <p style="color:#667; margin-top:0.4rem;">
                Sign in to access your dashboard
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password",
                                     placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                user = authenticate(username, password)
                if user:
                    # Persist user identity in session
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"]   = user["user_id"]
                    st.session_state["role_name"] = user["role_name"]
                    st.session_state["full_name"] = user["full_name"] or user["username"]
                    st.session_state["staff_id"]  = user.get("staff_id")

                    # For Doctor role: also resolve doctor_id
                    if user["role_name"] == "Doctor" and user.get("staff_id"):
                        doc_id = _load_doctor_id(user["staff_id"])
                        if doc_id:
                            st.session_state["doctor_id"] = doc_id
                        else:
                            st.warning("Your account is not linked to any doctor record.")
                    st.rerun()
                else:
                    st.error("Incorrect username or password. Please try again.")

        # Demo credentials (helpful for development / grading)
        with st.expander("🔑 Demo Credentials"):
            st.markdown("""
| Role | Username | Password |
|------|----------|----------|
| Admin / HR | `admin_super` | `super_secure_hash_123` |
| Doctor | `dr_james_wilson` | `hash123` |
| Receptionist | `recep_alice` | `hash123` |
| Accountant | `acc_bob` | `hash123` |
            """)


# ── HOME DASHBOARD (post-login) ───────────────────────────────────────────────
def show_home_stats():
    """Display key hospital metrics on the home screen after login."""
    conn = get_connection()
    if not conn:
        st.error("Cannot connect to the database.")
        return
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS n FROM patients")
    n_patients = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM appointments WHERE DATE(appt_date) = CURDATE()")
    n_appts = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM beds WHERE status = 'Available'")
    n_beds = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM invoices WHERE payment_status = 'Unpaid'")
    n_inv = cur.fetchone()["n"]
    cur.close()
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👤 Total Patients",          n_patients)
    c2.metric("📅 Appointments Today",       n_appts)
    c3.metric("🛏️ Available Beds",           n_beds)
    c4.metric("💳 Pending Invoices",         n_inv)


# ── MAIN ROUTER ───────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in", False):
    show_login_page()

else:
    role      = st.session_state["role_name"]
    full_name = st.session_state["full_name"]

    # Sidebar: user info + DB status + logout
    with st.sidebar:
        st.markdown("# 🏥 HMS")
        st.markdown("---")
        st.markdown(f"**👤 {full_name}**")
        st.caption(f"Role: {role}")
        st.markdown("---")
        conn_check = get_connection()
        if conn_check:
            st.success("🟢 Database Connected")
            conn_check.close()
        else:
            st.error("🔴 Database Offline")
        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            logout()

    # Route to the correct module based on authenticated role
    if role == "Admin":
        st.title(f"🏥 Welcome, {full_name}")
        show_home_stats()
        st.markdown("---")
        from modules import hr
        hr.run()

    elif role == "Doctor":
        from modules import doctor
        doctor.run()

    elif role == "Receptionist":
        from modules import receptionist
        receptionist.run()

    elif role == "Accountant":
        from modules import accountant
        accountant.run()

    else:
        st.warning(f"Role **'{role}'** does not have a configured dashboard.")