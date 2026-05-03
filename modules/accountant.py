import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from config import get_connection


def run():
    st.title("💰 Accountant Dashboard")

    # Resolve executor identity from session state (set during login)
    executor_id = st.session_state.get("user_id", 2)

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "💳 Pending Invoices",
        "📜 Payment History",
        "📊 Financial Report",
        "🏥 Insurance Management"
    ])

    # ── TAB 1: PENDING INVOICES ───────────────────────────────────────────────
    with tab1:
        st.subheader("Pending Invoices")
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT i.invoice_id, i.invoice_date,
                   COALESCE(p_a.full_name,  p_ad.full_name)   AS patient_name,
                   COALESCE(p_a.patient_id, p_ad.patient_id)  AS patient_id,
                   i.total_amount, i.appt_id, i.admission_id
            FROM invoices i
            LEFT JOIN appointments appt ON i.appt_id      = appt.appt_id
            LEFT JOIN patients p_a      ON appt.patient_id = p_a.patient_id
            LEFT JOIN admissions adm    ON i.admission_id  = adm.admission_id
            LEFT JOIN patients p_ad     ON adm.patient_id  = p_ad.patient_id
            WHERE i.payment_status = 'Unpaid'
            ORDER BY i.invoice_date DESC
        """)
        pending = cur.fetchall()
        cur.close(); conn.close()

        if not pending:
            st.success("✅ No pending invoices at this time.")
        else:
            for inv in pending:
                # Look up active insurance for this patient
                coverage = 0.0
                conn2 = get_connection()
                if conn2 and inv["patient_id"]:
                    cur2 = conn2.cursor(dictionary=True)
                    cur2.execute("""
                        SELECT coverage_rate FROM insurance
                        WHERE patient_id = %s AND expiry_date >= CURDATE()
                        LIMIT 1
                    """, (inv["patient_id"],))
                    ins_row = cur2.fetchone()
                    if ins_row:
                        coverage = float(ins_row["coverage_rate"])
                    cur2.close(); conn2.close()

                gross = float(inv["total_amount"] or 0)
                net   = gross * (1 - coverage)
                inv_type = "Outpatient" if inv["appt_id"] else "Inpatient"

                with st.expander(
                    f"🧾 Invoice #{inv['invoice_id']} — "
                    f"{inv['patient_name'] or 'N/A'} — {inv_type}"
                ):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Gross Amount",           f"${gross:,.2f}")
                    c2.metric("Insurance Coverage",      f"{coverage*100:.0f}%")
                    # Net shown here is a preview — net_amount is stored in DB only after payment
                    c3.metric("Estimated Net Payable",  f"${net:,.2f}")

                    # Show prescription details if outpatient invoice
                    if inv["appt_id"]:
                        conn3 = get_connection()
                        if conn3:
                            cur3 = conn3.cursor(dictionary=True)
                            cur3.execute("""
                                SELECT m.med_name, pd.dosage, pd.quantity,
                                       m.price, (m.price * pd.quantity) AS subtotal
                                FROM medical_records mr
                                JOIN prescriptions pr ON mr.record_id = pr.record_id
                                JOIN presc_details  pd ON pr.presc_id  = pd.presc_id
                                JOIN medicines      m  ON pd.med_id    = m.med_id
                                WHERE mr.appt_id = %s
                            """, (inv["appt_id"],))
                            items = cur3.fetchall()
                            cur3.close(); conn3.close()
                            if items:
                                df_items = pd.DataFrame(items)
                                df_items.columns = [
                                    "Medicine", "Dosage", "Qty",
                                    "Unit Price", "Subtotal"
                                ]
                                st.dataframe(df_items, use_container_width=True,
                                             hide_index=True)

                    c_pay, c_cancel = st.columns(2)
                    if c_pay.button(
                        f"✅ Mark as Paid #{inv['invoice_id']}",
                        key=f"pay_{inv['invoice_id']}"
                    ):
                        try:
                            c = get_connection()
                            cu = c.cursor()
                            # sp_pay_invoice checks RBAC (Accountant role required)
                            cu.callproc("sp_pay_invoice",
                                        [inv["invoice_id"], executor_id])
                            c.commit(); cu.close(); c.close()
                            # Trigger trg_release_bed_after_payment fires for
                            # admission-based invoices → bed released, admission closed
                            st.success(
                                f"Invoice #{inv['invoice_id']} marked as Paid."
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Payment failed: {e}")

                    if c_cancel.button(
                        f"❌ Cancel #{inv['invoice_id']}",
                        key=f"cancel_{inv['invoice_id']}"
                    ):
                        try:
                            c = get_connection()
                            cu = c.cursor()
                            cu.execute(
                                "UPDATE invoices SET payment_status = 'Cancelled'"
                                " WHERE invoice_id = %s",
                                (inv["invoice_id"],)
                            )
                            c.commit(); cu.close(); c.close()
                            st.warning(f"Invoice #{inv['invoice_id']} cancelled.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Cancellation failed: {e}")

    # ── TAB 2: PAYMENT HISTORY ────────────────────────────────────────────────
    with tab2:
        st.subheader("Payment History")
        c1, c2 = st.columns(2)
        date_from = c1.date_input("From:", value=date(2023, 1, 1))
        date_to   = c2.date_input("To:",   value=date.today())

        conn = get_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT i.invoice_id, i.invoice_date, i.payment_status,
                       COALESCE(p_a.full_name, p_ad.full_name) AS patient_name,
                       i.total_amount,
                       i.net_amount
                FROM invoices i
                LEFT JOIN appointments appt ON i.appt_id      = appt.appt_id
                LEFT JOIN patients p_a      ON appt.patient_id = p_a.patient_id
                LEFT JOIN admissions adm    ON i.admission_id  = adm.admission_id
                LEFT JOIN patients p_ad     ON adm.patient_id  = p_ad.patient_id
                WHERE i.payment_status IN ('Paid','Refunded','Cancelled')
                  AND DATE(i.invoice_date) BETWEEN %s AND %s
                ORDER BY i.invoice_date DESC
            """, (date_from, date_to))
            paid = cur.fetchall()
            cur.close(); conn.close()

            if paid:
                df = pd.DataFrame(paid)
                df.columns = ["ID", "Date", "Status", "Patient",
                              "Gross Amount ($)", "Net Amount ($)"]
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Revenue is the sum of net_amount (post-insurance actual collected)
                # Fall back to total_amount for legacy rows where net_amount is NULL
                total_paid = sum(
                    float(r["net_amount"] or r["total_amount"] or 0)
                    for r in paid if r["payment_status"] == "Paid"
                )
                st.metric("💰 Total Net Revenue in Period", f"${total_paid:,.2f}")
                st.caption("Revenue is based on net_amount (after insurance). "
                           "Legacy rows without net_amount fall back to gross.")

                # Refund section
                st.markdown("---")
                st.markdown("**Process Refund:**")
                refund_opts = {
                    f"#{r['invoice_id']} — {r['patient_name']}": r["invoice_id"]
                    for r in paid if r["payment_status"] == "Paid"
                }
                if refund_opts:
                    chosen_refund = st.selectbox("Select invoice to refund:",
                                                 list(refund_opts.keys()))
                    if st.button("↩️ Process Refund"):
                        try:
                            c = get_connection()
                            cu = c.cursor()
                            cu.execute(
                                "UPDATE invoices SET payment_status = 'Refunded'"
                                " WHERE invoice_id = %s",
                                (refund_opts[chosen_refund],)
                            )
                            c.commit(); cu.close(); c.close()
                            st.success("Refund processed successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Refund failed: {e}")
                else:
                    st.info("No paid invoices available for refund in this period.")
            else:
                st.info("No invoices found for the selected date range.")

    # ── TAB 3: FINANCIAL REPORT ───────────────────────────────────────────────
    with tab3:
        st.subheader("Financial Report")
        c1, c2 = st.columns(2)
        sel_month = c1.selectbox("Month:", list(range(1, 13)),
                                 index=datetime.now().month - 1)
        sel_year  = c2.number_input("Year:", min_value=2020, max_value=2030,
                                    value=datetime.now().year)

        if st.button("📊 Generate Monthly Report"):
            conn = get_connection()
            if conn:
                cur = conn.cursor(dictionary=True)
                try:
                    # sp_get_monthly_revenue enforces RBAC (Accountant or Admin)
                    cur.callproc("sp_get_monthly_revenue",
                                 [int(sel_month), int(sel_year), executor_id])
                    for rs in cur.stored_results():
                        row = rs.fetchone()
                        if row:
                            mc1, mc2, mc3 = st.columns(3)
                            revenue = float(row.get("total_revenue") or 0)
                            n_inv   = row.get("total_invoices", 0) or 1
                            mc1.metric(
                                f"Revenue — {sel_month}/{sel_year}",
                                f"${revenue:,.2f}"
                            )
                            mc2.metric("Invoices Collected", n_inv)
                            mc3.metric("Average per Invoice",
                                       f"${revenue/n_inv:,.2f}")
                        rs.fetchall() # Exhaust the result set to prevent Unread result error
                except Exception as e:
                    st.error(f"Report generation failed: {e}")
                
                # Fetch daily breakdown for the selected month
                try:
                    cur.execute("""
                        SELECT DAY(invoice_date) AS day,
                               SUM(COALESCE(net_amount, total_amount)) AS daily_revenue
                        FROM invoices
                        WHERE payment_status = 'Paid'
                          AND MONTH(invoice_date) = %s
                          AND YEAR(invoice_date) = %s
                        GROUP BY day
                        ORDER BY day
                    """, (int(sel_month), int(sel_year)))
                    daily_data = cur.fetchall()
                    
                    # Always display a chart with all days of the month
                    _, num_days = calendar.monthrange(int(sel_year), int(sel_month))
                    all_days = {day: 0.0 for day in range(1, num_days + 1)}
                    
                    if daily_data:
                        for r in daily_data:
                            all_days[r["day"]] = float(r["daily_revenue"] or 0)
                            
                    st.markdown(f"**Daily Revenue Trend — {sel_month}/{sel_year}**")
                    df_daily = pd.DataFrame(list(all_days.items()), columns=["Day", "Revenue ($)"])
                    st.bar_chart(df_daily.set_index("Day")["Revenue ($)"])
                except Exception as e:
                    st.error(f"Could not load daily chart: {e}")
                    
                cur.close(); conn.close()

        # 12-month revenue trend chart
        st.markdown("---")
        st.markdown("**Revenue Trend — Last 12 Months**")
        conn = get_connection()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT YEAR(invoice_date)  AS yr,
                       MONTH(invoice_date) AS mo,
                       -- Use net_amount (actual collected) when available;
                       -- fall back to total_amount for rows paid before Option B
                       SUM(COALESCE(net_amount, total_amount)) AS revenue
                FROM invoices
                WHERE payment_status = 'Paid'
                  AND invoice_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                GROUP BY yr, mo
                ORDER BY yr, mo
            """)
            trend = cur.fetchall()
            cur.close(); conn.close()

            if trend:
                df_trend = pd.DataFrame(trend)
                df_trend["Month"] = df_trend.apply(
                    lambda r: f"{int(r['mo'])}/{int(r['yr'])}", axis=1
                )
                df_trend["Revenue ($)"] = df_trend["revenue"].astype(float)
                st.bar_chart(df_trend.set_index("Month")["Revenue ($)"])
            else:
                st.info("No revenue data available yet.")

    # ── TAB 4: INSURANCE MANAGEMENT ──────────────────────────────────────────
    with tab4:
        st.subheader("Health Insurance Management")
        conn = get_connection()
        if not conn:
            st.error("Cannot connect to the database."); return
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT i.insurance_id, p.full_name AS patient_name,
                   p.patient_id, i.provider,
                   i.coverage_rate, i.expiry_date
            FROM insurance i
            JOIN patients p ON i.patient_id = p.patient_id
            ORDER BY i.expiry_date ASC
        """)
        ins_list = cur.fetchall()
        cur.close(); conn.close()

        if not ins_list:
            st.info("No insurance records found.")
            return

        today = date.today()
        for ins in ins_list:
            exp     = ins["expiry_date"]
            expired = (exp < today) if exp else True
            icon    = "🔴" if expired else "🟢"

            with st.expander(
                f"{icon} {ins['patient_name']} — "
                f"{ins['provider']} (ID: {ins['insurance_id']})"
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("Coverage Rate",  f"{float(ins['coverage_rate'])*100:.0f}%")
                c2.metric("Expiry Date",    str(exp))
                c3.write("🔴 **Expired**" if expired else "🟢 **Active**")

                # Inline form to update coverage rate or extend expiry
                with st.form(f"form_ins_{ins['insurance_id']}"):
                    new_rate = st.slider(
                        "Update Coverage Rate (%):", 0, 100,
                        int(float(ins["coverage_rate"]) * 100)
                    )
                    new_exp = st.date_input("Extend Expiry To:", value=exp)
                    if st.form_submit_button("💾 Update Insurance"):
                        try:
                            c = get_connection()
                            cu = c.cursor()
                            cu.execute(
                                "UPDATE insurance"
                                " SET coverage_rate = %s, expiry_date = %s"
                                " WHERE insurance_id = %s",
                                (new_rate / 100, str(new_exp), ins["insurance_id"])
                            )
                            c.commit(); cu.close(); c.close()
                            st.success("Insurance record updated successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Update failed: {e}")
