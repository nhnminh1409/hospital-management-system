import streamlit as st
import pandas as pd
from config import get_connection

def run():
    st.title("🛡️ System Administration")
    
    tab1, tab2, tab3 = st.tabs([
        "📊 System Overview",
        "🔑 Login History",
        "📜 Master Audit Log"
    ])

    # ── TAB 1: SYSTEM OVERVIEW ───────────────────────────────────────────────
    with tab1:
        st.subheader("Hospital System Statistics")
        conn = get_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            
            # Count users by role
            cur.execute("""
                SELECT r.role_name, COUNT(u.user_id) as count 
                FROM roles r 
                LEFT JOIN users u ON r.role_id = u.role_id 
                GROUP BY r.role_name
            """)
            role_counts = cur.fetchall()
            
            # Recent system activity count
            cur.execute("SELECT COUNT(*) as count FROM audit_logs WHERE timestamp > DATE_SUB(NOW(), INTERVAL 24 HOUR)")
            recent_logs = cur.fetchone()['count']
            
            cur.close(); conn.close()

            c1, c2 = st.columns(2)
            c1.metric("24h System Actions", recent_logs)
            
            st.markdown("**User Distribution by Role**")
            if role_counts:
                df_roles = pd.DataFrame(role_counts)
                st.bar_chart(df_roles.set_index("role_name"))

    # ── TAB 2: LOGIN HISTORY ──────────────────────────────────────────────────
    with tab2:
        st.subheader("User Login Tracking")
        conn = get_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT u.username, s.full_name, r.role_name, a.timestamp
                FROM audit_logs a
                JOIN users u ON a.user_id = u.user_id
                LEFT JOIN staff s ON u.user_id = s.user_id
                JOIN roles r ON u.role_id = r.role_id
                WHERE a.action = 'User Logged In'
                ORDER BY a.timestamp DESC
            """)
            logins = cur.fetchall()
            cur.close(); conn.close()

            if logins:
                df_logins = pd.DataFrame(logins)
                df_logins.columns = ["Username", "Full Name", "Role", "Login Time"]
                
                # Add "Login #" logic
                df_logins = df_logins.sort_values(["Username", "Login Time"])
                df_logins["Login #"] = df_logins.groupby("Username").cumcount() + 1
                
                # Display most recent first
                df_logins = df_logins.sort_values("Login Time", ascending=False)
                
                st.dataframe(df_logins[["Login #", "Username", "Full Name", "Role", "Login Time"]], 
                             use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.markdown("**Top Active Users (Login Frequency)**")
                freq = df_logins["Username"].value_counts().reset_index()
                freq.columns = ["Username", "Total Logins"]
                st.dataframe(freq, use_container_width=True, hide_index=True)
            else:
                st.info("No login logs found yet.")

    # ── TAB 3: MASTER AUDIT LOG ───────────────────────────────────────────────
    with tab3:
        st.subheader("Global Activity Audit Trail")
        conn = get_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT a.log_id, u.username, a.action, a.timestamp
                FROM audit_logs a
                JOIN users u ON a.user_id = u.user_id
                ORDER BY a.timestamp DESC
                LIMIT 100
            """)
            all_logs = cur.fetchall()
            cur.close(); conn.close()

            if all_logs:
                df_all = pd.DataFrame(all_logs)
                df_all.columns = ["Log ID", "User", "Action Description", "Timestamp"]
                st.dataframe(df_all, use_container_width=True, hide_index=True)
            else:
                st.info("No system logs recorded yet.")
