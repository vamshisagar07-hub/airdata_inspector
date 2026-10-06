# 📡 AirData Inspector
### Multi-Spectrum Spatial Signal Analytics & Campus Wi-Fi/Cellular Telemetry Profiling

**AirData Inspector** is a comprehensive Python and Streamlit application designed for wireless network analysis and spatial RF profiling. It bridges Computer Networks laboratory experiments (OS wireless interrogation, automated ICMP QoS profiling, packet capture) with Data Science spatial interpolation (2D Inverse Distance Weighting - IDW).

---

## 🚀 Key Features

1. **🧭 Visual Onboarding & Academic Reference**:
   - Interactive flowcharts, mathematical models, and syllabus mapping (Tasks 8b, 11b, 12b).
   - Signal quality thresholds for Wi-Fi RSSI (dBm) and Cellular 4G/5G RSRP (dBm).

2. **⚡ Dual-Spectrum Live Telemetry Monitor**:
   - Programmatic OS wireless interface inspection (`netsh wlan` on Windows, `nmcli` on Linux, `airport` on macOS).
   - Automated ICMP ping routines measuring Latency (RTT ms), Jitter (ms), and Packet Loss (%).
   - Integrated simulated telemetry fallback generator for offline testing or simulated campus walks.

3. **🗺️ Multi-Spectrum Spatial Heatmap Engine**:
   - 2D Inverse Distance Weighting (IDW) interpolation using SciPy.
   - Dual-spectrum side-by-side heatmaps (Wi-Fi RSSI vs Cellular RSRP).
   - Optimal Network Decision Matrix overlay (Wi-Fi vs Mobile handover recommendations).
   - Dead-zone identification and coverage attenuation analysis.

4. **📈 Cross-Spectrum Telemetry Correlation & QoS Regression Suite**:
   - Pearson correlation analysis ($r$) and regression plots connecting signal degradation to link latency, jitter, and packet loss.
   - Dynamic Composite Network Health Scoring:
     $$\text{Health Score} = 100 - (\text{Loss \%} \times 0.5) - (\text{Jitter ms} \times 0.3) - (\text{RTT Penalty} \times 0.2)$$

5. **📁 Dataset & Survey Waypoint Manager**:
   - Interactive data table with custom zone filtering and metrics summary.
   - CSV export and import capabilities for mobile war-driving logs.

---

## 🛠️ Tech Stack & Dependencies

- **Python 3.10+**
- **Streamlit**: Web dashboard interface
- **Pandas & NumPy**: Data processing and statistical matrices
- **SciPy**: 2D spatial interpolation (`scipy.interpolate.griddata`)
- **Matplotlib & Seaborn**: Multi-spectrum heatmaps and correlation regressions

---

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <REPO_URL>
   cd "CN glob"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the dashboard:**
   ```bash
   streamlit run app.py
   ```
   Open your browser at `http://localhost:8501`.

---

## 📂 Project Structure

```text
├── app.py                      # Main Streamlit dashboard application
├── collector.py                # OS telemetry acquisition & synthetic generators
├── analytics.py                # IDW spatial interpolation & visualization engine
├── requirements.txt            # Python dependencies
├── sample_data.csv             # Synthetic campus telemetry dataset
├── implements.md               # Technical implementation specifications
├── wifi heatmap.md             # Core network & spatial algorithm guidelines
└── final.md                    # Project requirements summary
```

---

## 📄 License
MIT License. Developed for Academic Research and Network Engineering demonstrations.
