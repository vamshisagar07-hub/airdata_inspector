# TASK: Build "AirData Inspector" - Multi-Spectrum Spatial Signal Analytics & Campus Wi-Fi/Cellular Dashboard

Act as a Principal Software Engineer & Network Data Scientist. Build a production-grade, self-contained Python Streamlit application titled **"AirData Inspector: Multi-Spectrum Spatial Signal Analytics & Telemetry Profiling for Campus Wi-Fi and Cellular Networks"**.

This project bridges GRIET Computer Networks Lab syllabus requirements (Tasks 8b, 11b, and 12b) with Data Science spatial interpolation (IDW). Contextual implementation details, mathematical models, and operational blueprints are governed by the local documentation files in the workspace:
1. `CN glob/implements.md` (System execution specifications, onboarding guidelines, and multi-spectrum unification)
2. `CN glob/wifi heatmap.md` (Core Wi-Fi NIC inspection architecture, ICMP ping automated collection, and spatial interpolation specifications)

---

## 1. DETAILED SPECIFICATIONS & ARCHITECTURE

### A. Onboarding & Visual User Instructions Panel (`implements.md`)
- Include an interactive **"🧭 User Guide & Onboarding Instructions"** tab at the top of the main dashboard:
  1. **Visual System Architecture**: ASCII flowchart rendering data flow from OS Network Interface Cards (NIC) and cellular telemetry to the Inverse Distance Weighting (IDW) interpolation engine.
  2. **4-Step Execution Walkthrough**:
     - *Step 1: Grid Calibration*: Define physical room/floor dimensions ($X \times Y$ meters).
     - *Step 2: Dual Telemetry Capture*: Fetch active Wi-Fi NIC metrics via system calls and record cellular RSRP values.
     - *Step 3: Spatial Sampling*: Map live readings to discrete grid coordinates.
     - *Step 4: Heatmap Generation*: Execute SciPy spatial interpolation to reveal signal dead zones and optimal coverage.
  3. **Signal Strength Scale Reference**:
     - **Wi-Fi RSSI (dBm)**: Excellent ($> -50$), Good ($-50$ to $-70$), Dead Zone ($< -80$).
     - **Cellular RSRP (dBm)**: Excellent ($> -80$), Fair ($-80$ to $-100$), Cellular Dead Zone ($< -110$).

### B. Live Telemetry & Dual-Spectrum Network Engine (`wifi heatmap.md` & `implements.md`)
1. **Wi-Fi NIC Inspection (CN Task 11b)**:
   - Interface programmatically with OS wireless network adapters (`netsh wlan show interfaces` on Windows / `nmcli` or `airport` on Unix/macOS) via Python `subprocess`.
   - Extract real-time metrics: **RSSI (dBm)**, **SSID**, **BSSID**, **Operating Channel/Frequency (2.4 GHz vs 5 GHz)**, and **Link Speed**.
   - Provide an automatic fallback synthetic generator if no active Wi-Fi interface is detected to ensure seamless live demonstrations.

2. **Network Performance Utilities (CN Task 8b)**:
   - Automate background ICMP ping routines to gateway addresses (`8.8.8.8` or local router).
   - Log **Round-Trip Time (RTT Latency in ms)**, **Jitter**, and **Packet Loss (%)**.

3. **Cellular Spectrum Integration**:
   - Capture cellular signal power (**RSRP in dBm**), network operator name (e.g., Airtel, Jio), and network type (5G / 4G LTE).
   - Allow manual coordinate entry or CSV import from cellular logger mobile applications (NetVelocity / Network Cell Info).

### C. Data Science & Spatial Analytics Engine
1. **Spatial Interpolation**:
   - Utilize SciPy's `griddata` (Inverse Distance Weighting / Cubic method) to project discrete telemetry points onto a continuous 2D plane overlaying the campus floor plan.
2. **Composite Network Health Index**:
   - Calculate coordinate-specific reliability scores:
     $$\text{Health Score} = 100 - (\text{Packet Loss \%} \times 0.5) - (\text{Jitter ms} \times 0.3) - (\text{RTT Penalty} \times 0.2)$$
3. **Unified Optimal Coverage Overlay Map**:
   - Compare Wi-Fi RSSI and Cellular RSRP across all grid coordinates $(X, Y)$ and render a single decision matrix map indicating whether **Wi-Fi** or **Mobile Network** offers superior connectivity at each position.

---

## 2. APPLICATION DASHBOARD STRUCTURE (`app.py`)

1. **Tab 1: 🧭 Quick Start & Onboarding Guide**:
   - Step-by-step operation guide, syllabus mapping (Tasks 8b, 11b, 12b), and signal classification reference keys.
2. **Tab 2: ⚡ Live Telemetry Monitor**:
   - Real-time gauge metrics for RSSI, RSRP, Ping RTT, Packet Loss, and raw system command outputs for faculty evaluation.
3. **Tab 3: 🗺️ Multi-Spectrum Heatmap Analytics**:
   - Toggle view modes: `[Side-by-Side Heatmaps (Wi-Fi vs Cell)]` | `[Optimal Signal Overlay Map]` | `[Dead-Zone Identifier]`.
4. **Tab 4: 📈 Telemetry Correlation Engine**:
   - Scatter plots and regression models illustrating the direct relationship between low RSSI ($\le -80\text{ dBm}$) and increased packet loss/jitter.
5. **Tab 5: 📁 Dataset & Export Utility**:
   - Interactive Pandas DataFrame displaying `[X, Y, WiFi_RSSI, Cell_RSRP, Latency, Loss_Pct, Health_Score]` with a CSV export trigger.

---

## 3. PROJECT DIRECTORY STRUCTURE

Ensure the generated project maintains the following layout:
```text
├── CN glob/
│   ├── implements.md
│   └── wifi heatmap.md
├── app.py
├── collector.py
├── analytics.py
├── sample_data.csv
└── requirements.txt