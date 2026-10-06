"""
AirData Inspector: Multi-Spectrum Spatial Signal Analytics & Campus Wi-Fi/Cellular Dashboard
Academic Project for GRIET Computer Networks Lab (Tasks 8b, 11b, 12b) + Data Science Spatial IDW Interpolation.
"""

import sys
import os
import io
import time
import pandas as pd
import numpy as np
import streamlit as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import collector
import analytics

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="AirData Inspector | Multi-Spectrum Signal Analytics",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Modern Theme CSS Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top Header Banner */
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    }
    .hero-title {
        color: #f8fafc;
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        line-height: 1.5;
        margin-bottom: 12px;
    }
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .tech-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .pill-blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .pill-emerald { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .pill-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .pill-purple { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
    
    /* Metrics and Status Cards */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    .metric-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    
    /* Flowchart & Code Boxes */
    .flowchart-box {
        background: #0f172a;
        color: #38bdf8;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        line-height: 1.45;
        overflow-x: auto;
    }
    
    /* Instruction Steps */
    .step-card {
        background: #1e293b;
        border-left: 4px solid #3b82f6;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin-bottom: 12px;
    }
    .step-header {
        font-weight: 700;
        color: #e2e8f0;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }
    .step-desc {
        color: #94a3b8;
        font-size: 0.85rem;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Top Hero Header Banner ---
st.markdown("""
<div class="hero-container">
    <div class="hero-title">
        <span>📡</span> AirData Inspector
    </div>
    <div class="hero-subtitle">
        <strong>Multi-Spectrum Spatial Signal Analytics & Telemetry Profiling for Campus Wi-Fi & Cellular Networks</strong><br>
        Bridging Computer Networks Laboratory Experiments (Tasks 8b, 11b & 12b) with Data Science Inverse Distance Weighting (IDW) Spatial Analytics.
    </div>
    <div class="badge-container">
        <span class="tech-pill pill-blue">CN Task 11b: OS Wireless NIC Interrogation</span>
        <span class="tech-pill pill-emerald">CN Task 8b: Automated ICMP Ping QoS Profiling</span>
        <span class="tech-pill pill-amber">Dual-Spectrum: Wi-Fi RSSI vs Cellular 5G/4G RSRP</span>
        <span class="tech-pill pill-purple">Spatial Analytics: 2D Inverse Distance Weighting (IDW)</span>
    </div>
</div>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
if "survey_data" not in st.session_state:
    csv_path = "sample_data.csv"
    if os.path.exists(csv_path):
        st.session_state.survey_data = pd.read_csv(csv_path)
    else:
        st.session_state.survey_data = collector.generate_campus_seed_dataset(45)
        st.session_state.survey_data.to_csv(csv_path, index=False)

if "last_wifi" not in st.session_state:
    st.session_state.last_wifi = collector.get_wifi_telemetry()

if "last_ping" not in st.session_state:
    st.session_state.last_ping = collector.get_ping_metrics("8.8.8.8", count=2)


# --- Sidebar Configuration & Calibration ---
with st.sidebar:
    st.header("⚙️ System Configuration")
    
    st.subheader("1. Telemetry Capture Mode")
    telemetry_mode = st.radio(
        "Source Mode:",
        ["⚡ Live OS Hardware Capture", "🧪 Simulated Telemetry Generator"],
        index=0,
        help="Choose whether to query actual OS network cards via netsh/nmcli or run in offline simulated demonstration mode."
    )
    force_sim = (telemetry_mode == "🧪 Simulated Telemetry Generator")

    st.subheader("2. Campus Grid Calibration")
    col_w, col_h = st.columns(2)
    with col_w:
        floor_width = st.number_input("Floor Width (m)", min_value=10.0, max_value=100.0, value=30.0, step=5.0)
    with col_h:
        floor_height = st.number_input("Floor Length (m)", min_value=10.0, max_value=100.0, value=20.0, step=5.0)

    st.subheader("3. Spatial Interpolation Engine")
    grid_resolution = st.slider("Meshgrid Density (Points)", min_value=30, max_value=100, value=50, step=10)
    idw_power = st.slider("IDW Distance Decay Power (p)", min_value=1.0, max_value=4.0, value=2.0, step=0.5,
                          help="Higher power p concentrates signal around sample points; lower p creates smoother spatial diffusion.")

    st.subheader("4. Handover Decision Thresholds")
    handover_delta = st.slider(
        "Decision Margin (ΔQ %)",
        min_value=2.0, max_value=25.0, value=8.0, step=1.0,
        help="Signal quality difference required to trigger a decisive Wi-Fi vs Cellular dominance classification."
    )
    wifi_dead_thresh = st.slider("Wi-Fi Dead Zone Cutoff (dBm)", -95, -70, -82, 1)
    cell_dead_thresh = st.slider("Cellular Dead Zone Cutoff (dBm)", -120, -95, -108, 1)

    st.markdown("---")
    st.caption("GRIET Computer Networks & IoT Department • AirData Inspector Engine v2.4")


# --- Cached Interpolation Runner ---
@st.cache_data(show_spinner=False)
def run_spatial_mesh_computation(df: pd.DataFrame, width: float, height: float, density: int, power: float, delta: float, w_cutoff: float, c_cutoff: float):
    # Compute mesh coordinates
    nx = density
    ny = int(density * (height / width))
    x_lin = np.linspace(0, width, nx)
    y_lin = np.linspace(0, height, ny)
    grid_x, grid_y = np.meshgrid(x_lin, y_lin)

    # Perform IDW spatial interpolation
    grid_wifi = analytics.interpolate_spatial_grid(df["X"].values, df["Y"].values, df["WiFi_RSSI"].values, grid_x, grid_y, method="idw", idw_power=power)
    grid_cell = analytics.interpolate_spatial_grid(df["X"].values, df["Y"].values, df["Cell_RSRP"].values, grid_x, grid_y, method="idw", idw_power=power)

    # Compute Optimal Coverage Overlay and Stats
    decision_map, delta_q, stats = analytics.compute_optimal_coverage_overlay(
        grid_wifi, grid_cell, delta_threshold=delta, dead_zone_cutoff_wifi=w_cutoff, dead_zone_cutoff_cell=c_cutoff
    )

    return grid_x, grid_y, grid_wifi, grid_cell, decision_map, delta_q, stats


# --- Main Dashboard Navigation Tabs ---
tabs = st.tabs([
    "🧭 Onboarding & Syllabus Guide",
    "⚡ Live Telemetry Monitor",
    "🗺️ Multi-Spectrum Heatmap Analytics",
    "📈 Telemetry Correlation Engine",
    "📁 Dataset & Survey Manager"
])


# ==============================================================================
# TAB 1: ONBOARDING & SYLLABUS GUIDE
# ==============================================================================
with tabs[0]:
    st.markdown("### 🧭 System Architecture & Onboarding Walkthrough")
    
    col_guide1, col_guide2 = st.columns([1.1, 0.9])
    
    with col_guide1:
        st.markdown("#### 🏗️ End-to-End System Architecture Flowchart")
        st.markdown("""
<div class="flowchart-box">
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│     OS Hardware Subprocesses    │     │    Mobile Cellular Telemetry    │
│  (netsh / nmcli / airport)      │     │  (NetVelocity / Field Surveys)  │
└────────────────┬────────────────┘     └────────────────┬────────────────┘
                 │                                       │
                 ▼                                       ▼
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│   Task 11b: Wi-Fi NIC Parsing   │     │    Cellular RF Profiler (dBm)   │
│   RSSI, SSID, BSSID, Freq, Link │     │    RSRP, RSRQ, SINR, Tech, Band │
└────────────────┬────────────────┘     └────────────────┬────────────────┘
                 │                                       │
                 ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│      Task 8b: ICMP Ping Performance Engine (RTT Latency, Jitter, Loss)  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│     Data Science Spatial Engine: Inverse Distance Weighting (IDW)       │
│                Z(s) = Σ [w_i * z_i] / Σ [w_i],  w_i = 1 / d(s, s_i)^p   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
             ┌───────────────────────┴───────────────────────┐
             ▼                                               ▼
┌───────────────────────────────────────┐   ┌───────────────────────────────────┐
│  Composite Health Score Index (0-100) │   │  Optimal Coverage Overlay Map     │
│  Health = 100 - 0.5*Loss - 0.3*Jitter │   │  Wi-Fi Dominant vs Cellular 5G    │
└───────────────────────────────────────┘   └───────────────────────────────────┘
</div>
""", unsafe_allow_html=True)

        st.markdown("#### 🎓 Computer Networks Lab Syllabus Integration")
        syllabus_df = pd.DataFrame({
            "Lab Task": ["Task 8b", "Task 11b", "Task 12b", "Data Science (IDW)"],
            "Topic / Focus": [
                "Network Performance & QoS",
                "Wireless NIC Interrogation",
                "Wireless Propagation & Heatmaps",
                "Spatial RF Interpolation"
            ],
            "Implementation Mechanism in AirData Inspector": [
                "Automated background ICMP Ping routines parsing RTT Latency, Jitter, and Loss %.",
                "Subprocess calls to OS native network drivers (netsh wlan) parsing RSSI, BSSID, and Channel.",
                "Continuous 2D contour mapping overlaying campus architectural block layout.",
                "Vectorized Shepard's Inverse Distance Weighting to model path loss and building attenuation."
            ]
        })
        st.dataframe(syllabus_df, use_container_width=True, hide_index=True)

    with col_guide2:
        st.markdown("#### 🚀 4-Step Operational Execution Walkthrough")
        
        st.markdown("""
<div class="step-card">
    <div class="step-header">Step 1: Grid Calibration</div>
    <div class="step-desc">Configure the physical floor dimensions (Width × Length in meters) in the sidebar. Default campus layout is calibrated to 30m × 20m.</div>
</div>
<div class="step-card">
    <div class="step-header">Step 2: Dual Telemetry Capture</div>
    <div class="step-desc">Query active hardware Wi-Fi NIC signals via OS system calls and combine with real-time mobile cellular RSRP measurements.</div>
</div>
<div class="step-card">
    <div class="step-header">Step 3: Spatial Sampling</div>
    <div class="step-desc">Record discrete readings at designated coordinate waypoints across labs, corridors, server vault, and balconies.</div>
</div>
<div class="step-card">
    <div class="step-header">Step 4: Multi-Spectrum Heatmap Generation</div>
    <div class="step-desc">Execute IDW spatial interpolation to render side-by-side spectrum comparisons, dead-zone alerts, and the Optimal Coverage Overlay.</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("#### 📊 Standard Spectrum Classification Benchmarks")
        bench_df = pd.DataFrame({
            "Quality Band": ["Excellent", "Good / Fair", "Marginal", "Dead Zone"],
            "Wi-Fi RSSI (dBm)": ["> -50 dBm", "-50 to -70 dBm", "-70 to -80 dBm", "< -80 dBm"],
            "Cellular RSRP (dBm)": ["> -80 dBm", "-80 to -95 dBm", "-95 to -108 dBm", "< -108 dBm"],
            "User Experience": ["Full 4K Streaming / Gigabit", "Smooth HD Video / Voice", "Intermittent Buffering", "Connection Drops / High Loss"]
        })
        st.dataframe(bench_df, use_container_width=True, hide_index=True)

        st.info("💡 **Tip**: Switch to **Tab 2 (Live Telemetry Monitor)** to inspect your live physical network adapter or test logging live survey points.")


# ==============================================================================
# TAB 2: LIVE TELEMETRY MONITOR
# ==============================================================================
with tabs[1]:
    st.markdown("### ⚡ Real-Time Network Telemetry & NIC Interrogation")
    
    col_action1, col_action2, col_action3 = st.columns([1.5, 1.2, 1.3])
    with col_action1:
        if st.button("🔄 Query Active Network Interfaces Now", type="primary", use_container_width=True):
            st.session_state.last_wifi = collector.get_wifi_telemetry(force_simulation=force_sim)
            st.session_state.last_ping = collector.get_ping_metrics("8.8.8.8", count=3, force_simulation=force_sim)
            st.toast("Telemetry refreshed from OS network drivers!", icon="✅")

    with col_action2:
        ping_target = st.text_input("Ping Target Host", value="8.8.8.8", help="DNS resolver or campus gateway")
    with col_action3:
        cell_carrier_sel = st.selectbox("Cellular Operator Profile", ["Jio 5G NSA", "Airtel 5G Plus", "Vodafone Idea 4G", "BSNL 4G"])

    wifi_data = st.session_state.last_wifi
    ping_data = st.session_state.last_ping
    cell_data = collector.get_cellular_telemetry(carrier=cell_carrier_sel)

    # Top Live Metrics Gauge Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        w_rssi = wifi_data.get("rssi_dbm", -65.0)
        badge = "🟢" if w_rssi > -65 else ("🟡" if w_rssi > -80 else "🔴")
        st.metric(label=f"Wi-Fi RSSI {badge}", value=f"{w_rssi} dBm", delta=f"{wifi_data.get('signal_pct', 0)}% Quality")
    with m2:
        c_rsrp = cell_data.get("rsrp_dbm", -88.0)
        badge_c = "🟢" if c_rsrp > -85 else ("🟡" if c_rsrp > -105 else "🔴")
        st.metric(label=f"Cellular RSRP {badge_c}", value=f"{c_rsrp} dBm", delta=f"{cell_data.get('tech')}")
    with m3:
        rtt_val = ping_data.get("rtt_avg_ms", 22.0)
        st.metric(label="ICMP Ping Latency", value=f"{rtt_val} ms", delta=f"Min: {ping_data.get('rtt_min_ms', 0)}ms")
    with m4:
        jitter_val = ping_data.get("jitter_ms", 2.1)
        st.metric(label="Packet Jitter", value=f"{jitter_val} ms", delta=f"±{round(jitter_val*0.8, 1)}ms dev")
    with m5:
        loss_val = ping_data.get("packet_loss_pct", 0.0)
        loss_delta = "Clean" if loss_val == 0 else f"{loss_val}% Loss"
        st.metric(label="Packet Loss Rate", value=f"{loss_val}%", delta=loss_delta, delta_color="inverse" if loss_val > 0 else "normal")

    st.markdown("---")

    col_live_left, col_live_right = st.columns([1.1, 0.9])
    
    with col_live_left:
        st.markdown("#### 📶 Wireless Adapter Hardware Parameters (Task 11b)")
        adapter_table = {
            "Hardware Field": ["Connection State", "Connected SSID", "Access Point BSSID", "Radio Technology", "Channel / Band", "Interface Link Rate", "Hardware Adapter", "Data Mode"],
            "Extracted Value": [
                wifi_data.get("status", "Unknown").upper(),
                str(wifi_data.get("ssid", "N/A")),
                str(wifi_data.get("bssid", "N/A")),
                str(wifi_data.get("radio_type", "802.11")),
                f"Channel {wifi_data.get('channel', 'N/A')} ({wifi_data.get('band', 'N/A')})",
                f"Rx: {wifi_data.get('rx_rate_mbps', 0)} Mbps / Tx: {wifi_data.get('tx_rate_mbps', 0)} Mbps",
                str(wifi_data.get("adapter", "NIC Adapter")),
                "⚡ Live Physical Hardware" if not wifi_data.get("is_simulated") else "🧪 Synthetic Generator Fallback"
            ]
        }
        st.dataframe(pd.DataFrame(adapter_table), use_container_width=True, hide_index=True)

        with st.expander("🔍 Faculty Verification: Inspect Raw OS Shell Outputs", expanded=False):
            st.markdown("**1. Raw Wi-Fi Driver Output (`netsh wlan show interfaces`):**")
            st.code(wifi_data.get("raw_output", "No output captured"), language="text")
            st.markdown(f"**2. Raw ICMP Ping Execution (`ping {ping_target}`):**")
            st.code(ping_data.get("raw_output", "No output captured"), language="text")

    with col_live_right:
        st.markdown("#### 📍 Survey Waypoint Coordinate Logger")
        st.caption("Capture the current live metrics and tag them to a physical coordinate on the floor plan.")
        
        with st.form("log_sample_form"):
            col_x, col_y = st.columns(2)
            with col_x:
                sample_x = st.number_input("Floor X (meters)", min_value=0.0, max_value=floor_width, value=12.5, step=0.5)
            with col_y:
                sample_y = st.number_input("Floor Y (meters)", min_value=0.0, max_value=floor_height, value=10.0, step=0.5)
            
            sample_zone = st.selectbox(
                "Campus Room / Zone Tag",
                ["CN Lab 1 (Near AP1)", "CN Lab 2 (Adjoining)", "Central Corridor", "Server & Storage (Shielded)", "Seminar Hall (Near AP2)", "Faculty Cabins", "East Balcony / Outdoor Terrace", "West Stairwell & Fire Exit"]
            )
            
            submit_sample = st.form_submit_button("📌 Commit & Log Telemetry Sample", type="primary", use_container_width=True)
            if submit_sample:
                # Calculate composite health score
                score = analytics.compute_health_score(loss_val, jitter_val, rtt_val)
                new_row = {
                    "X": sample_x,
                    "Y": sample_y,
                    "Zone": sample_zone,
                    "WiFi_SSID": wifi_data.get("ssid", "Live_AP"),
                    "WiFi_RSSI": w_rssi,
                    "Cell_Operator": cell_carrier_sel,
                    "Cell_Tech": cell_data.get("tech", "5G"),
                    "Cell_RSRP": c_rsrp,
                    "Latency_ms": rtt_val,
                    "Jitter_ms": jitter_val,
                    "Packet_Loss_Pct": loss_val,
                    "Health_Score": score
                }
                st.session_state.survey_data = pd.concat([st.session_state.survey_data, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state.survey_data.to_csv("sample_data.csv", index=False)
                st.toast(f"Point logged at ({sample_x}m, {sample_y}m) with Health Score: {score}!", icon="🎯")
                st.rerun()


# ==============================================================================
# TAB 3: MULTI-SPECTRUM HEATMAP ANALYTICS (FLAGSHIP OVERLAY)
# ==============================================================================
with tabs[2]:
    st.markdown("### 🗺️ Unified Multi-Spectrum Heatmap & Optimal Coverage Overlay")
    st.caption("Parallel spatial processing of Wi-Fi RSSI and Cellular RSRP across the campus grid layout.")

    df_active = st.session_state.survey_data
    
    # Run cached IDW spatial computation
    with st.spinner("Computing Inverse Distance Weighting (IDW) continuous surface..."):
        grid_x, grid_y, grid_wifi, grid_cell, decision_map, delta_q, stats = run_spatial_mesh_computation(
            df_active, floor_width, floor_height, grid_resolution, idw_power, handover_delta, wifi_dead_thresh, cell_dead_thresh
        )

    # Top KPI Banner for Coverage Dominance
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #10b981;">
            <div class="metric-label">📶 Wi-Fi Optimal Area</div>
            <div class="metric-value" style="color: #34d399;">{stats['wifi_dominant_pct']}%</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #f59e0b;">
            <div class="metric-label">📱 Cellular Optimal Area</div>
            <div class="metric-value" style="color: #fbbf24;">{stats['cellular_dominant_pct']}%</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #06b6d4;">
            <div class="metric-label">⚖️ Balanced Coverage</div>
            <div class="metric-value" style="color: #38bdf8;">{stats['balanced_coverage_pct']}%</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #ef4444;">
            <div class="metric-label">⚠️ Dual Dead Zone</div>
            <div class="metric-value" style="color: #f87171;">{stats['dual_dead_zone_pct']}%</div>
        </div>
        """, unsafe_allow_html=True)
    with k5:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #8b5cf6;">
            <div class="metric-label">🎯 Active Waypoints</div>
            <div class="metric-value" style="color: #c084fc;">{len(df_active)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # View Mode Selector
    map_mode = st.radio(
        "Select Spatial Heatmap View Mode:",
        [
            "🌟 Optimal Coverage Overlay Map (Flagship Decision Engine)",
            "📊 Side-by-Side Dual Heatmaps (Wi-Fi RSSI vs Cellular RSRP)",
            "⚠️ Spectrum Dead-Zone & Attenuation Vulnerability Map"
        ],
        horizontal=True
    )

    if "Optimal Coverage Overlay" in map_mode:
        st.markdown("#### 🌟 Unified Optimal Coverage Overlay Map")
        st.info("💡 **How to interpret this map:** Green regions indicate where **Wi-Fi** offers superior throughput and lower latency. Orange/Amber regions indicate where **Mobile Cellular Data (5G/4G)** is stronger (e.g. balconies and terrace areas where AP signal is attenuated). Cyan represents **Balanced Dual-Coverage**, and Red indicates **Dual Dead Zones**.")
        
        fig_overlay = analytics.generate_optimal_coverage_overlay_figure(
            df_active, grid_x, grid_y, decision_map, delta_q, stats, floor_w=floor_width, floor_h=floor_height
        )
        st.pyplot(fig_overlay, use_container_width=True)
        plt.close(fig_overlay)

    elif "Side-by-Side" in map_mode:
        st.markdown("#### 📊 Dual-Spectrum Comparative Spatial Heatmaps")
        st.caption("Left: 2.4/5GHz Wi-Fi RSSI contour surface. Right: Cellular 5G/4G RSRP contour surface.")
        
        fig_side = analytics.generate_side_by_side_heatmap_figure(
            df_active, grid_x, grid_y, grid_wifi, grid_cell, floor_w=floor_width, floor_h=floor_height
        )
        st.pyplot(fig_side, use_container_width=True)
        plt.close(fig_side)

    else:
        st.markdown("#### ⚠️ Campus Coverage Dead-Zone & Attenuation Map")
        st.caption("Hatched red patterns depict Wi-Fi dropouts (< -82 dBm), while diagonal amber lines show cellular attenuation.")
        
        fig_dead = analytics.generate_dead_zone_identifier_figure(
            df_active, grid_x, grid_y, grid_wifi, grid_cell, floor_w=floor_width, floor_h=floor_height
        )
        st.pyplot(fig_dead, use_container_width=True)
        plt.close(fig_dead)

    # Technical Handover & Roaming Insights
    with st.expander("📋 Multi-Spectrum Handover & Network Engineering Insights", expanded=True):
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            st.markdown("**🏢 RF Physical Propagation Analysis:**")
            st.markdown(f"""
            - **Wi-Fi Dominance Zone ({stats['wifi_dominant_pct']}% of floor)**: High-speed line-of-sight coverage radiating from AP1 (CN Lab 1) and AP2 (Seminar Hall). Average RSSI is `{stats['avg_wifi_rssi']} dBm`.
            - **Cellular Handover Zone ({stats['cellular_dominant_pct']}% of floor)**: Outdoor terrace and exterior walkways have direct line-of-sight to the macro cell tower, making 5G significantly stronger than indoor Wi-Fi.
            """)
        with col_in2:
            st.markdown("**🛠️ Recommended Infrastructure Optimizations:**")
            st.markdown(f"""
            - **Server Vault Attenuation**: Heavy concrete shielding creates a localized dead zone `{stats['dual_dead_zone_pct']}%`. Recommend deploying an Ethernet drop or micro-AP.
            - **Seamless Roaming Protocol**: Configure 802.11k/802.11v client-steering with a `-75 dBm` handover threshold before cellular fallback.
            """)


# ==============================================================================
# TAB 4: TELEMETRY CORRELATION ENGINE
# ==============================================================================
with tabs[3]:
    st.markdown("### 📈 Cross-Spectrum Telemetry Correlation & QoS Regression Suite")
    st.caption("Validates the physical principle: RF Signal Degraded (< -80 dBm) correlates directly with higher Packet Loss and Jitter.")

    df_active = st.session_state.survey_data

    fig_corr = analytics.generate_correlation_plots(df_active)
    st.pyplot(fig_corr, use_container_width=True)
    plt.close(fig_corr)

    st.markdown("#### 🔍 Statistical Correlation Coefficients (Pearson r)")
    corr_cols = ["WiFi_RSSI", "Cell_RSRP", "Latency_ms", "Jitter_ms", "Packet_Loss_Pct", "Health_Score"]
    corr_matrix = df_active[corr_cols].corr()

    c_left, c_right = st.columns([1.2, 0.8])
    with c_left:
        st.dataframe(
            corr_matrix.style.background_gradient(cmap="coolwarm", vmin=-1.0, vmax=1.0).format("{:.3f}"),
            use_container_width=True
        )
    with c_right:
        r_loss = corr_matrix.loc["WiFi_RSSI", "Packet_Loss_Pct"]
        r_lat = corr_matrix.loc["WiFi_RSSI", "Latency_ms"]
        st.markdown(f"""
        **Key Findings:**
        - **RSSI vs Packet Loss**: Strong negative correlation ($r = {r_loss:.3f}$), confirming signal attenuation causes retransmissions and frame drops.
        - **RSSI vs Latency**: Negative correlation ($r = {r_lat:.3f}$), demonstrating link layer rate back-off at lower signal-to-noise ratios.
        - **Health Score**: Positively correlated with RSSI and inversely correlated with packet loss and jitter.
        """)


# ==============================================================================
# TAB 5: DATASET & SURVEY MANAGER
# ==============================================================================
with tabs[4]:
    st.markdown("### 📁 Dataset & Survey Waypoint Manager")
    st.caption("Inspect, filter, export, or upload spatial telemetry logs.")

    df_active = st.session_state.survey_data

    # Filter Toolbar
    f1, f2, f3 = st.columns([1.2, 1.2, 1.6])
    with f1:
        zones_all = ["All Zones"] + sorted(list(df_active["Zone"].unique()))
        sel_zone = st.selectbox("Filter by Zone:", zones_all)
    with f2:
        min_health = st.slider("Minimum Health Score:", 0, 100, 0)
    with f3:
        search_kw = st.text_input("Search SSID / Operator:", "")

    # Apply Filters
    df_filtered = df_active.copy()
    if sel_zone != "All Zones":
        df_filtered = df_filtered[df_filtered["Zone"] == sel_zone]
    df_filtered = df_filtered[df_filtered["Health_Score"] >= min_health]
    if search_kw:
        df_filtered = df_filtered[
            df_filtered["WiFi_SSID"].str.contains(search_kw, case=False, na=False) |
            df_filtered["Cell_Operator"].str.contains(search_kw, case=False, na=False)
        ]

    st.dataframe(
        df_filtered,
        use_container_width=True,
        column_config={
            "Health_Score": st.column_config.ProgressColumn(
                "Health Score", min_value=0, max_value=100, format="%d"
            ),
            "WiFi_RSSI": st.column_config.NumberColumn("Wi-Fi RSSI (dBm)", format="%.1f"),
            "Cell_RSRP": st.column_config.NumberColumn("Cellular RSRP (dBm)", format="%.1f"),
            "Packet_Loss_Pct": st.column_config.NumberColumn("Loss %", format="%.1f%%"),
        }
    )

    st.markdown("---")

    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        st.markdown("#### 📥 Export Dataset")
        csv_buffer = df_active.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Active Dataset (CSV)",
            data=csv_buffer,
            file_name=f"airdata_telemetry_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )

    with col_exp2:
        st.markdown("#### 📤 Import Survey CSV")
        uploaded_file = st.file_uploader("Upload NetVelocity / Network Cell Info CSV", type=["csv"])
        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                # Verify required columns or map
                req_cols = {"X", "Y", "WiFi_RSSI", "Cell_RSRP"}
                if req_cols.issubset(set(uploaded_df.columns)):
                    if "Health_Score" not in uploaded_df.columns:
                        uploaded_df["Health_Score"] = [
                            analytics.compute_health_score(row.get("Packet_Loss_Pct", 0), row.get("Jitter_ms", 1), row.get("Latency_ms", 20))
                            for _, row in uploaded_df.iterrows()
                        ]
                    st.session_state.survey_data = uploaded_df
                    st.session_state.survey_data.to_csv("sample_data.csv", index=False)
                    st.success(f"Loaded {len(uploaded_df)} custom survey points successfully!")
                    st.rerun()
                else:
                    st.error(f"CSV missing mandatory columns: {req_cols - set(uploaded_df.columns)}")
            except Exception as e:
                st.error(f"Error parsing CSV: {e}")

    with col_exp3:
        st.markdown("#### 🔄 Reset Dataset")
        if st.button("⚠️ Reset to Campus Default Seed", use_container_width=True):
            st.session_state.survey_data = collector.generate_campus_seed_dataset(45)
            st.session_state.survey_data.to_csv("sample_data.csv", index=False)
            st.toast("Restored default campus seed dataset!", icon="🔄")
            st.rerun()

st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 40px; padding: 12px; border-top: 1px solid #1e293b;">
    AirData Inspector • Multi-Spectrum Spatial Signal Analytics Dashboard • GRIET Computer Networks Lab Demonstration
</div>
""", unsafe_allow_html=True)
