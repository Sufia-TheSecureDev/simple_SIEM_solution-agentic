# import streamlit as st
# import psycopg2
# import pandas as pd

# conn = psycopg2.connect(
#     host=st.secrets["DB_HOST"],
#     database=st.secrets["DB_NAME"],
#     user=st.secrets["DB_USER"],
#     password=st.secrets["DB_PASS"],
#     port=st.secrets["DB_PORT"]
# )

# query = "SELECT * FROM devices ORDER BY created_at DESC"

# df = pd.read_sql(query, conn)

# st.title("SIEM Solution")

# st.dataframe(df)

"""
SIEM Dashboard — Streamlit
Deploy to streamlit.io, secrets go in .streamlit/secrets.toml
"""

import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SIEM Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    body { background-color: #0d1117; }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .severity-critical { color: #ff4444; font-weight: bold; }
    .severity-high     { color: #ff8800; font-weight: bold; }
    .severity-medium   { color: #ffcc00; font-weight: bold; }
    .severity-low      { color: #44cc44; }
    .stDataFrame { font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# ── DB connection ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"],
        port=st.secrets["DB_PORT"]
    )

@st.cache_data(ttl=30)  # refresh every 30 seconds
def load_data():
    conn = get_conn()

    devices = pd.read_sql("SELECT * FROM devices ORDER BY created_at DESC", conn)

    events = pd.read_sql("""
        SELECT e.id, d.hostname, d.ip_address, e.event_type,
               e.severity, e.description, e.created_at
        FROM events e
        JOIN devices d ON e.device_id = d.id
        ORDER BY e.created_at DESC
        LIMIT 200
    """, conn)

    alerts = pd.read_sql("""
        SELECT a.id, a.status, a.notified_at, a.created_at,
               e.event_type, e.severity, e.description,
               d.hostname
        FROM alerts a
        JOIN events e ON a.event_id = e.id
        JOIN devices d ON e.device_id = d.id
        ORDER BY a.created_at DESC
        LIMIT 100
    """, conn)

    severity_counts = pd.read_sql("""
        SELECT severity, COUNT(*) as count
        FROM events
        GROUP BY severity
    """, conn)

    event_type_counts = pd.read_sql("""
        SELECT event_type, COUNT(*) as count
        FROM events
        GROUP BY event_type
        ORDER BY count DESC
    """, conn)

    return devices, events, alerts, severity_counts, event_type_counts

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🛡️ SIEM Dashboard")
st.caption(f"Last refreshed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
st.divider()

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    devices, events, alerts, severity_counts, event_type_counts = load_data()
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

# ── KPI Row ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

def sev_count(sev):
    row = severity_counts[severity_counts["severity"] == sev]
    return int(row["count"].values[0]) if not row.empty else 0

col1.metric("🖥️ Devices",        len(devices))
col2.metric("📋 Total Events",   len(events))
col3.metric("🔴 Critical",       sev_count("critical"))
col4.metric("🟠 High",           sev_count("high"))
col5.metric("🚨 Open Alerts",    len(alerts[alerts["status"] == "open"]) if not alerts.empty else 0)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🚨 Alerts", "📋 Events", "🖥️ Devices", "📊 Stats"])

# ── Tab 1: Alerts ─────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Open Alerts")
    if alerts.empty:
        st.info("No alerts yet.")
    else:
        open_alerts = alerts[alerts["status"] == "open"]
        if open_alerts.empty:
            st.success("✅ No open alerts!")
        else:
            for _, row in open_alerts.iterrows():
                color = {
                    "critical": "🔴", "high": "🟠",
                    "medium": "🟡",   "low": "🟢"
                }.get(row["severity"], "⚪")
                with st.expander(
                    f"{color} [{row['severity'].upper()}] {row['event_type']} — {row['hostname']} "
                    f"| {pd.to_datetime(row['created_at']).strftime('%Y-%m-%d %H:%M')}"
                ):
                    st.write("**AI Analysis:**", row["description"])
                    st.write("**Notified at:**", row["notified_at"])

        st.subheader("All Alerts")
        st.dataframe(alerts, use_container_width=True)

# ── Tab 2: Events ─────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Recent Events (last 200)")

    # Filter controls
    col_a, col_b = st.columns(2)
    sev_filter  = col_a.multiselect("Filter by Severity",
                                     ["critical","high","medium","low"],
                                     default=["critical","high","medium","low"])
    type_filter = col_b.multiselect("Filter by Type",
                                     events["event_type"].unique().tolist() if not events.empty else [],
                                     default=events["event_type"].unique().tolist() if not events.empty else [])

    filtered = events[
        events["severity"].isin(sev_filter) &
        events["event_type"].isin(type_filter)
    ] if not events.empty else events

    st.dataframe(filtered, use_container_width=True)

# ── Tab 3: Devices ────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Registered Devices")
    st.dataframe(devices, use_container_width=True)

# ── Tab 4: Stats ──────────────────────────────────────────────────────────────
with tab4:
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Events by Severity")
        if not severity_counts.empty:
            st.bar_chart(severity_counts.set_index("severity")["count"])
        else:
            st.info("No data yet.")

    with col_r:
        st.subheader("Events by Type")
        if not event_type_counts.empty:
            st.bar_chart(event_type_counts.set_index("event_type")["count"])
        else:
            st.info("No data yet.")

# ── Auto-refresh ──────────────────────────────────────────────────────────────
st.divider()
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

st.caption("Dashboard auto-caches for 30s. Click Refresh for latest data.")
