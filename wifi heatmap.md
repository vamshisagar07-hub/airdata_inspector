# TASK: Build "AirData Inspector" - Dual-Spectrum Signal Analytics & Campus Wi-Fi/Cellular Heatmap Dashboard

Act as a Principal Software Engineer & Network Data Scientist. Build a fully functional, self-contained Python application and Streamlit dashboard titled **"AirData Inspector: Multi-Spectrum Spatial Signal Analytics & Telemetry Profiling for Campus Wi-Fi Networks"**. 

This application bridges Computer Networks concepts (Lab Tasks 8b & 11b) with Data Science spatial interpolation for a live academic project demonstration.

---

## 1. TECHNICAL ARCHITECTURE & REQUIREMENTS

### A. Live Network Telemetry Collector Engine (`collector.py`)
1. **Wi-Fi NIC Inspection (CN Task 11b)**:
   - Extract active Wi-Fi connection metrics using OS subprocesses (`netsh wlan show interfaces` for Windows or `nmcli` / `airport` for Linux/macOS).
   - Extract **RSSI / Signal Quality (%)**, converted to **dBm**, **SSID**, **BSSID**, **Channel/Frequency (2.4GHz vs 5GHz)**, and **Link Rate**.
   - Provide a synthetic telemetry fallback generator if live Wi-Fi is disconnected or permissions are limited, ensuring uninterrupted live demonstration.

2. **Network Performance Utilities (CN Task 8b)**:
   - Automate ICMP PING calls to gateway router (`8.8.8.8` or default gateway).
   - Measure **Round-Trip Time (RTT Latency in ms)**, **Jitter**, and **Packet Loss (%)**.

### B. Data Science & Spatial Interpolation Engine (`analytics.py`)
1. **Data Structuring**:
   - Maintain a DataFrame schema: `[X_coord, Y_coord, WiFi_RSSI_dBm, Cell_RSRP_dBm, Latency_ms, Packet_Loss_Pct, Health_Score]`.
2. **Mathematical Operations**:
   - **Inverse Distance Weighting (IDW)** & **SciPy `griddata`**: Interpolate discrete telemetry samples across a grid over a campus floor plan layout.
   - **Composite Health Score Formula**:
     $$\text{Health Score} = 100 - (\text{Loss\%} \times 0.5) - (\text{Jitter} \times 0.3) - (\text{RTT Penalty} \times 0.2)$$
   - Categorize signal zones: **Strong (Green)**, **Moderate (Yellow)**, **Dead Zone / High Loss (Red)**.

### C. Interactive Streamlit Presentation Dashboard (`app.py`)
1. **Sidebar Controls**:
   - Toggle between **Live Telemetry Capture Mode** and **Simulated Campus Grid Mode**.
   - Sliders for sample grid density, signal frequency selection (2.4 GHz vs 5 GHz), and attenuation threshold settings.
   - Dual-Spectrum toggle: Wi-Fi RSSI Map, Cellular RSRP Map, or Dual Health Score Index.

2. **Main Dashboard Tabs**:
   - **Tab 1: Live Telemetry Monitor (Task 8b & 11b)**: Real-time gauge metrics for RSSI, Ping Latency, Loss %, and raw command output log for faculty verification.
   - **Tab 2: 2D Spatial Heatmap Analytics**: SciPy-interpolated Matplotlib/Seaborn contour heatmaps overlaying a grid floor plan, marking router positions and identified dead-zones.
   - **Tab 3: Telemetry vs Loss Correlation Plots**: Seaborn scatter/regression plots showing low RSSI ($\le -80\text{ dBm}$) correlating with packet loss spikes and latency jitter.
   - **Tab 4: Dataset & Export**: Interactive Pandas table showing all telemetry logs with a button to export CSV.

---

## 2. PROJECT FILE STRUCTURE

Create the following file organization:
- `app.py` - Main Streamlit UI and dashboard layout.
- `collector.py` - Subprocess handlers for Wi-Fi NIC inspection and PING automation.
- `analytics.py` - SciPy spatial grid interpolation (IDW) and health score engine.
- `requirements.txt` - Dependencies (`streamlit`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`).
- `sample_data.csv` - Pre-populated spatial telemetry dataset for instant live demonstration.

---

## 3. EXECUTION INSTRUCTIONS

1. Install dependencies from `requirements.txt`.
2. Generate synthetic seed dataset `sample_data.csv` if missing.
3. Run `streamlit run app.py` and present the live interactive dashboard.