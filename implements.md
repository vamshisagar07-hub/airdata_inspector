# TASK: Build "AirData Inspector" - Unified Wi-Fi & Cellular Multi-Spectrum Spatial Analytics Dashboard with Onboarding Guide

Act as a Principal Software Engineer & Network Data Scientist. Build a production-grade, self-contained Python Streamlit application titled **"AirData Inspector: Multi-Spectrum Spatial Signal Analytics & Telemetry Profiling for Campus Wi-Fi and Cellular Networks"**.

This project bridges Computer Networks concepts (Lab Tasks 8b & 11b) with Data Science spatial interpolation (IDW) for a live GRIET academic presentation.

---

## 1. CORE FEATURES & REQUIREMENT EXTENSIONS

### A. Visual Onboarding & How-To-Use Walkthrough Panel
- Include a dedicated **"User Guide & Instructions"** expander panel or tab on top of the main dashboard containing:
  1. **Visual Flowchart**: Text/ASCII workflow diagram showing how data moves from OS drivers to spatial interpolation.
  2. **4-Step Operations Walkthrough**:
     - *Step 1: Calibration* (Set room dimensions X × Y meters).
     - *Step 2: Dual Data Capture* (Fetch active Wi-Fi NIC signals via OS + input mobile network RSRP readings).
     - *Step 3: Grid Sampling* (Record readings across floor plan coordinates).
     - *Step 4: Heatmap Generation* (Run IDW interpolation to reveal dead zones).
  3. **Spectrum Reference Key**:
     - **Wi-Fi RSSI (dBm)**: Excellent (> -50), Good (-50 to -70), Poor (< -80).
     - **Cellular RSRP (dBm)**: Excellent (> -80), Fair (-80 to -100), Cell Dead Zone (< -110).

### B. Unified Multi-Spectrum Architecture (Wi-Fi + Cellular in 1 View)
- Build a **Dual-Spectrum Side-by-Side & Overlay Engine**:
  1. **Wi-Fi Telemetry Collector (Task 11b & 8b)**: Programmatically fetches live Wi-Fi RSSI (dBm), SSID, BSSID, Link Rate, and PING latency/loss metrics via OS subprocesses (`netsh` / `airport` / `nmcli`).
  2. **Mobile Network Telemetry Collector**: Captures Cellular RSRP (dBm), Mobile Carrier (Airtel, Jio, etc.), and Band info (5G/4G LTE) via manual coordinate log or file import from mobile apps (NetVelocity / Network Cell Info).
  3. **Unified Dual Heatmap Visualizer**:
     - Render side-by-side spatial heatmaps comparing **Wi-Fi RSSI** vs. **Cellular RSRP**.
     - Render an **"Optimal Coverage Overlay Map"** showing which network (Wi-Fi vs Mobile) provides the strongest signal at every $(X, Y)$ coordinate in the room/campus block.

### C. Mathematical Analytics Engine
- **Inverse Distance Weighting (IDW) & SciPy `griddata`**: Interpolates signal values across unsampled grid areas.
- **Composite Network Health Index**:
  $$\text{Health Score} = 100 - (\text{Packet Loss \%} \times 0.5) - (\text{Jitter ms} \times 0.3) - (\text{Latency Penalty} \times 0.2)$$

---

## 2. DASHBOARD TAB STRUCTURE (`app.py`)

1. **Tab 1: 🧭 Quick Start & Visual Onboarding**:
   - Interactive visual guide, syllabus mappings (Tasks 8b, 11b, 12b), and step-by-step instructions.

2. **Tab 2: ⚡ Live Telemetry Monitor**:
   - Real-time gauge meters for Wi-Fi RSSI, Cellular RSRP, Ping RTT, and raw command logs for live faculty verification.

3. **Tab 3: 🗺️ Unified Multi-Spectrum Heatmaps (Wi-Fi + Cellular)**:
   - **View Mode Toggle**: [Side-by-Side Dual Heatmap] | [Optimal Signal Overlay Map] | [Dead-Zone Identifier].
   - Highlights exact locations where Wi-Fi drops but Cellular is strong, and vice-versa.

4. **Tab 4: 📈 Telemetry vs. Performance Correlation**:
   - Seaborn regression graphs showing low RSSI/RSRP ($\le -80\text{ dBm}$) correlating with higher packet loss and ping jitter.

5. **Tab 5: 📁 Dataset & Export**:
   - Interactive Pandas DataFrame showing combined telemetry logs `[X, Y, WiFi_RSSI, Cell_RSRP, Latency, Loss, Health_Score]` with a CSV export button.

---

## 3. PROJECT FILE STRUCTURE

Create the following file structure:
- `app.py`: Main Streamlit UI, onboarding guide, and layout.
- `collector.py`: Subprocess execution for Wi-Fi NIC inspection and ping tests + simulated cellular engine.
- `analytics.py`: IDW interpolation, overlay mapping logic, and score calculations.
- `requirements.txt`: Dependencies (`streamlit`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`).
- `sample_data.csv`: Pre-populated spatial dataset for quick demonstration.

---

## 4. EXECUTION INSTRUCTIONS

1. Install dependencies: `pip install -r requirements.txt`.
2. Generate synthetic `sample_data.csv` if missing.
3. Run `streamlit run app.py` and open the interactive dashboard.