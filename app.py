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
Sufia's SIEM Dashboard — Streamlit
Layout: left sidebar = device list, right panel = device detail + tabs
FIX: Device selection now properly filters right panel per selected device
"""

import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Sufia's SIEM Dashboard", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Sora:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #080c14; color: #c9d1d9; }
.siem-header { background: linear-gradient(135deg, #0d1f3c 0%, #0a1628 100%); border: 1px solid #1e3a5f; border-radius: 12px; padding: 20px 28px; margin-bottom: 20px; }
.siem-title { font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: 700; color: #58a6ff; margin: 0; }
.siem-subtitle { font-size: 0.78rem; color: #6e7f96; margin: 0; font-family: 'JetBrains Mono', monospace; }
.kpi-row { display: flex; gap: 12px; margin-bottom: 24px; }
.kpi-card { flex: 1; background: #0d1f3c; border: 1px solid #1e3a5f; border-radius: 10px; padding: 16px 20px; text-align: center; position: relative; overflow: hidden; }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.kpi-card.devices::before  { background: #58a6ff; }
.kpi-card.total::before    { background: #3fb950; }
.kpi-card.critical::before { background: #f85149; }
.kpi-card.high::before     { background: #e3b341; }
.kpi-card.alerts::before   { background: #bc8cff; }
.kpi-label { font-size: 0.7rem; color: #6e7f96; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; font-family: 'JetBrains Mono', monospace; }
.kpi-value { font-size: 2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.kpi-value.devices  { color: #58a6ff; }
.kpi-value.total    { color: #3fb950; }
.kpi-value.critical { color: #f85149; }
.kpi-value.high     { color: #e3b341; }
.kpi-value.alerts   { color: #bc8cff; }
.device-card { background: #0d1f3c; border: 1px solid #1e3a5f; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; }
.device-card.selected { border-color: #58a6ff; background: #112240; }
.device-hostname { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; font-weight: 600; color: #58a6ff; margin-bottom: 4px; }
.device-meta { font-size: 0.72rem; color: #6e7f96; }
.detail-card { background: #0d1f3c; border: 1px solid #1e3a5f; border-radius: 10px; padding: 20px 24px; margin-bottom: 20px; }
.detail-title { font-family: 'JetBrains Mono', monospace; font-size: 1rem; font-weight: 700; color: #58a6ff; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid #1e3a5f; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.detail-label { font-size: 0.68rem; color: #6e7f96; text-transform: uppercase; letter-spacing: 1px; font-family: 'JetBrains Mono', monospace; margin-bottom: 3px; }
.detail-value { font-size: 0.88rem; color: #e6edf3; font-weight: 500; }
.alert-card { background: #0d1f3c; border-left: 4px solid #f85149; border-radius: 0 8px 8px 0; padding: 14px 16px; margin-bottom: 10px; }
.alert-card.high   { border-left-color: #e3b341; }
.alert-card.medium { border-left-color: #3fb950; }
.alert-card.low    { border-left-color: #58a6ff; }
.alert-event { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; font-weight: 600; color: #e6edf3; margin-bottom: 6px; }
.alert-desc  { font-size: 0.78rem; color: #8b949e; line-height: 1.5; margin-bottom: 8px; }
.alert-meta  { font-size: 0.7rem; color: #6e7f96; font-family: 'JetBrains Mono', monospace; }
.section-label { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #6e7f96; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 1px solid #1e3a5f; }
.stButton > button { background: #1e3a5f !important; border: 1px solid #58a6ff !important; color: #58a6ff !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.78rem !important; border-radius: 6px !important; }
.stButton > button:hover { background: #58a6ff !important; color: #080c14 !important; }
.stTabs [data-baseweb="tab-list"] { background: #0d1f3c; border-radius: 8px 8px 0 0; border: 1px solid #1e3a5f; border-bottom: none; gap: 0; }
.stTabs [data-baseweb="tab"] { color: #6e7f96 !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.78rem !important; padding: 10px 20px !important; }
.stTabs [aria-selected="true"] { background: #112240 !important; color: #58a6ff !important; border-bottom: 2px solid #58a6ff !important; }
.stTabs [data-baseweb="tab-panel"] { background: #0a1628; border: 1px solid #1e3a5f; border-top: none; border-radius: 0 0 8px 8px; padding: 16px !important; }
hr { border-color: #1e3a5f !important; }
/* Hide default radio button circles */
div[data-testid="stRadio"] > div { gap: 0 !important; }
div[data-testid="stRadio"] label { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DB
# ══════════════════════════════════════════════════════════════════════════════
def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"], database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"], password=st.secrets["DB_PASS"],
        port=st.secrets["DB_PORT"]
    )

@st.cache_data(ttl=30)
def load_all():
    conn = get_conn()
    try:
        devices = pd.read_sql("""
            SELECT id, hostname, ip_address,
                   COALESCE(location, 'Unknown') as location,
                   COALESCE(timezone, 'UTC')     as timezone,
                   COALESCE(os, 'Unknown')       as os,
                   created_at
            FROM devices ORDER BY created_at DESC
        """, conn)

        events = pd.read_sql("""
            SELECT e.id, e.device_id, d.hostname, d.ip_address,
                   e.event_type, e.severity, e.description, e.created_at
            FROM events e
            JOIN devices d ON e.device_id = d.id
            ORDER BY e.created_at DESC
            LIMIT 1000
        """, conn)

        alerts = pd.read_sql("""
            SELECT a.id, a.status, a.notified_at, a.created_at,
                   e.event_type, e.severity, e.description,
                   e.device_id, d.hostname
            FROM alerts a
            JOIN events e ON a.event_id = e.id
            JOIN devices d ON e.device_id = d.id
            ORDER BY a.created_at DESC
            LIMIT 500
        """, conn)

        sev_counts = pd.read_sql(
            "SELECT severity, COUNT(*) as count FROM events GROUP BY severity", conn)

        type_counts = pd.read_sql("""
            SELECT event_type, COUNT(*) as count FROM events
            GROUP BY event_type ORDER BY count DESC
        """, conn)

        return devices, events, alerts, sev_counts, type_counts
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
try:
    devices, events, alerts, sev_counts, type_counts = load_all()
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

def sev_count(sev):
    r = sev_counts[sev_counts["severity"] == sev]
    return int(r["count"].values[0]) if not r.empty else 0

open_alerts_count = int((alerts["status"] == "open").sum()) if not alerts.empty else 0

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
now_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
st.markdown(f"""
<div class="siem-header">
    <p class="siem-title">🛡️ Sufia's SIEM Dashboard</p>
    <p class="siem-subtitle">Last refreshed: {now_str} &nbsp;|&nbsp; Monitoring {len(devices)} device(s)</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# KPI ROW
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card devices"><div class="kpi-label">Devices</div><div class="kpi-value devices">{len(devices)}</div></div>
    <div class="kpi-card total"><div class="kpi-label">Total Events</div><div class="kpi-value total">{len(events)}</div></div>
    <div class="kpi-card critical"><div class="kpi-label">Critical</div><div class="kpi-value critical">{sev_count('critical')}</div></div>
    <div class="kpi-card high"><div class="kpi-label">High</div><div class="kpi-value high">{sev_count('high')}</div></div>
    <div class="kpi-card alerts"><div class="kpi-label">Open Alerts</div><div class="kpi-value alerts">{open_alerts_count}</div></div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 3], gap="medium")

with col_left:
    st.markdown('<div class="section-label">Registered Devices</div>', unsafe_allow_html=True)

    if devices.empty:
        st.info("No devices registered yet.")
        selected_device_id = None
    else:
        # ── KEY FIX: use device ID as the selector value, not hostname ────────
        # This ensures unique selection even if two devices have same hostname
        device_id_list = devices["id"].tolist()

        # Build display labels for selectbox
        device_labels = {}
        for _, dev in devices.iterrows():
            dev_alerts_count = 0
            if not alerts.empty:
                dev_alerts_count = int((alerts[alerts["device_id"] == dev["id"]]["status"] == "open").sum())
            alert_tag = f" ⚠{dev_alerts_count}" if dev_alerts_count > 0 else " ●"
            device_labels[dev["id"]] = f"{dev['hostname']}{alert_tag}"

        # Use st.radio with device IDs — this is the KEY fix
        # format_func converts ID to display label
        selected_device_id = st.radio(
            label="select_device",
            options=device_id_list,
            format_func=lambda x: device_labels.get(x, str(x)),
            label_visibility="collapsed"
        )

        # Show device info cards below radio (cosmetic only)
        for _, dev in devices.iterrows():
            is_sel = dev["id"] == selected_device_id
            card_class = "device-card selected" if is_sel else "device-card"
            dev_open = 0
            if not alerts.empty:
                dev_open = int((alerts[alerts["device_id"] == dev["id"]]["status"] == "open").sum())
            badge = (f'<span style="color:#f85149;font-size:0.7rem">⚠ {dev_open} alerts</span>'
                     if dev_open > 0 else
                     '<span style="color:#3fb950;font-size:0.7rem">● online</span>')
            st.markdown(f"""
            <div class="{card_class}">
                <div class="device-hostname">{dev['hostname']}</div>
                <div class="device-meta">{dev['ip_address']}</div>
                <div class="device-meta">{dev['location']}</div>
                <div style="margin-top:5px">{badge}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — filtered strictly by selected_device_id
# ══════════════════════════════════════════════════════════════════════════════
with col_right:
    if selected_device_id is None or devices.empty:
        st.info("← Select a device from the left to view its details.")
    else:
        # Get the selected device row by ID — guaranteed unique
        dev_row = devices[devices["id"] == selected_device_id]
        if dev_row.empty:
            st.warning("Device not found.")
        else:
            dev = dev_row.iloc[0]

            # Filter events and alerts strictly by device_id
            dev_events = events[events["device_id"] == selected_device_id].copy() if not events.empty else pd.DataFrame()
            dev_alerts = alerts[alerts["device_id"] == selected_device_id].copy() if not alerts.empty else pd.DataFrame()

            # ── Device Detail Card ────────────────────────────────────────────
            st.markdown(f"""
            <div class="detail-card">
                <div class="detail-title">📡 Device Details — {dev['hostname']}</div>
                <div class="detail-grid">
                    <div>
                        <div class="detail-label">Hostname</div>
                        <div class="detail-value">{dev['hostname']}</div>
                    </div>
                    <div>
                        <div class="detail-label">IP Address</div>
                        <div class="detail-value">{dev['ip_address']}</div>
                    </div>
                    <div>
                        <div class="detail-label">Location</div>
                        <div class="detail-value">📍 {dev['location']}</div>
                    </div>
                    <div>
                        <div class="detail-label">Timezone</div>
                        <div class="detail-value">🕐 {dev['timezone']}</div>
                    </div>
                    <div>
                        <div class="detail-label">Operating System</div>
                        <div class="detail-value">💻 {dev['os']}</div>
                    </div>
                    <div>
                        <div class="detail-label">Registered At</div>
                        <div class="detail-value">{pd.to_datetime(dev['created_at']).strftime('%Y-%m-%d %H:%M')} UTC</div>
                    </div>
                    <div>
                        <div class="detail-label">Total Events</div>
                        <div class="detail-value">{len(dev_events)}</div>
                    </div>
                    <div>
                        <div class="detail-label">Open Alerts</div>
                        <div class="detail-value">{int((dev_alerts['status']=='open').sum()) if not dev_alerts.empty else 0}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Tabs ──────────────────────────────────────────────────────────
            tab_alerts, tab_events, tab_stats = st.tabs(["🚨 Alerts", "📋 Events", "📊 Stats"])

            # ── Alerts Tab ────────────────────────────────────────────────────
            with tab_alerts:
                if dev_alerts.empty:
                    st.info("No alerts for this device.")
                else:
                    open_a   = dev_alerts[dev_alerts["status"] == "open"]
                    closed_a = dev_alerts[dev_alerts["status"] != "open"]

                    if open_a.empty:
                        st.success("✅ No open alerts for this device!")
                    else:
                        st.markdown(f'<div class="section-label">Open Alerts ({len(open_a)})</div>', unsafe_allow_html=True)
                        for _, row in open_a.iterrows():
                            sev   = row["severity"]
                            emoji = {"critical":"🔴","high":"🟠","medium":"🟡","low":"🟢"}.get(sev,"⚪")
                            time_ = pd.to_datetime(row["created_at"]).strftime("%Y-%m-%d %H:%M UTC")
                            st.markdown(f"""
                            <div class="alert-card {sev}">
                                <div class="alert-event">{emoji} [{sev.upper()}] {row['event_type']}</div>
                                <div class="alert-desc">{row['description']}</div>
                                <div class="alert-meta">🕐 {time_} &nbsp;|&nbsp; Host: {row['hostname']}</div>
                            </div>
                            """, unsafe_allow_html=True)

                    if not closed_a.empty:
                        with st.expander(f"Resolved Alerts ({len(closed_a)})"):
                            st.dataframe(closed_a[["event_type","severity","created_at","status"]],
                                         use_container_width=True)

            # ── Events Tab ────────────────────────────────────────────────────
            with tab_events:
                if dev_events.empty:
                    st.info("No events for this device.")
                else:
                    col_a, col_b = st.columns(2)
                    sev_filter  = col_a.multiselect("Severity",
                        ["critical","high","medium","low"],
                        default=["critical","high","medium","low"],
                        key=f"sev_{selected_device_id}")
                    type_filter = col_b.multiselect("Event Type",
                        dev_events["event_type"].unique().tolist(),
                        default=dev_events["event_type"].unique().tolist(),
                        key=f"typ_{selected_device_id}")

                    filtered = dev_events[
                        dev_events["severity"].isin(sev_filter) &
                        dev_events["event_type"].isin(type_filter)
                    ]
                    st.caption(f"Showing {len(filtered)} of {len(dev_events)} events for {dev['hostname']}")
                    st.dataframe(
                        filtered[["id","event_type","severity","description","created_at"]],
                        use_container_width=True
                    )

            # ── Stats Tab ─────────────────────────────────────────────────────
            with tab_stats:
                if dev_events.empty:
                    st.info("No data yet.")
                else:
                    col_l, col_r = st.columns(2)
                    with col_l:
                        st.markdown("**Events by Severity**")
                        sev_d = dev_events.groupby("severity").size().reset_index(name="count")
                        st.bar_chart(sev_d.set_index("severity")["count"])
                    with col_r:
                        st.markdown("**Events by Type**")
                        typ_d = dev_events.groupby("event_type").size().reset_index(name="count")
                        st.bar_chart(typ_d.set_index("event_type")["count"])
