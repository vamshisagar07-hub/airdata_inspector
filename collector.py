"""
AirData Inspector: Telemetry Collector Engine
Interfaces with OS Network Interface Cards (NIC), automates ICMP ping routines,
and models cellular RF telemetry (RSRP, carrier, band).
"""

import sys
import os
import re
import time
import math
import random
import subprocess
import pandas as pd
import numpy as np


def get_wifi_telemetry(force_simulation: bool = False, seed_offset: int = 0) -> dict:
    """
    Interrogates OS Wireless NIC using native command-line utilities.
    - Windows: netsh wlan show interfaces
    - Linux: nmcli dev wifi / iwconfig
    - macOS: airport -I
    Provides automatic synthetic fallback when no hardware NIC is connected.
    """
    if not force_simulation:
        if sys.platform.startswith("win"):
            try:
                cmd = "netsh wlan show interfaces"
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=4,
                    errors="ignore"
                )
                output = proc.stdout or ""
                if "State" in output and ("connected" in output.lower() or "associé" in output.lower()):
                    # Parse netsh fields
                    state_match = re.search(r"^\s*State\s*:\s*(.+)$", output, re.M)
                    ssid_match = re.search(r"^\s*SSID\s*:\s*(.+)$", output, re.M)
                    bssid_match = re.search(r"^\s*(?:AP BSSID|BSSID)\s*:\s*(.+)$", output, re.M)
                    signal_match = re.search(r"^\s*Signal\s*:\s*(\d+)%", output, re.M)
                    rssi_match = re.search(r"^\s*Rssi\s*:\s*(-?\d+)", output, re.M)
                    channel_match = re.search(r"^\s*Channel\s*:\s*(\d+)", output, re.M)
                    band_match = re.search(r"^\s*Band\s*:\s*(.+)$", output, re.M)
                    radio_match = re.search(r"^\s*Radio type\s*:\s*(.+)$", output, re.M)
                    rx_match = re.search(r"^\s*Receive rate \(Mbps\)\s*:\s*([\d\.]+)", output, re.M)
                    tx_match = re.search(r"^\s*Transmit rate \(Mbps\)\s*:\s*([\d\.]+)", output, re.M)
                    desc_match = re.search(r"^\s*Description\s*:\s*(.+)$", output, re.M)

                    signal_pct = float(signal_match.group(1)) if signal_match else 75.0
                    
                    # Direct RSSI or calculate from Signal % (Signal% / 2 - 100)
                    if rssi_match:
                        rssi_dbm = float(rssi_match.group(1))
                    else:
                        rssi_dbm = round((signal_pct / 2.0) - 100.0, 1)

                    band_str = band_match.group(1).strip() if band_match else ("5 GHz" if (channel_match and int(channel_match.group(1)) > 14) else "2.4 GHz")
                    
                    return {
                        "status": "connected",
                        "ssid": ssid_match.group(1).strip() if ssid_match else "Campus_WLAN",
                        "bssid": bssid_match.group(1).strip() if bssid_match else "00:1A:2B:3C:4D:5E",
                        "signal_pct": signal_pct,
                        "rssi_dbm": rssi_dbm,
                        "channel": int(channel_match.group(1)) if channel_match else 36,
                        "band": band_str,
                        "radio_type": radio_match.group(1).strip() if radio_match else "802.11ax/ac",
                        "rx_rate_mbps": float(rx_match.group(1)) if rx_match else 300.0,
                        "tx_rate_mbps": float(tx_match.group(1)) if tx_match else 300.0,
                        "adapter": desc_match.group(1).strip() if desc_match else "Wireless Adapter",
                        "is_simulated": False,
                        "raw_output": output.strip(),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            except Exception:
                pass  # Fall through to synthetic generator

        elif sys.platform.startswith("linux"):
            try:
                proc = subprocess.run(
                    ["nmcli", "-t", "-f", "active,ssid,bssid,signal,chan", "dev", "wifi"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                output = proc.stdout or ""
                for line in output.splitlines():
                    if line.startswith("yes:"):
                        parts = line.split(":")
                        ssid = parts[1] if len(parts) > 1 else "Campus_WLAN"
                        bssid = parts[2] if len(parts) > 2 else "00:1A:2B:3C:4D:5E"
                        sig_pct = float(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 70.0
                        chan = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 36
                        rssi_dbm = round((sig_pct / 2.0) - 100.0, 1)
                        return {
                            "status": "connected",
                            "ssid": ssid,
                            "bssid": bssid,
                            "signal_pct": sig_pct,
                            "rssi_dbm": rssi_dbm,
                            "channel": chan,
                            "band": "5 GHz" if chan > 14 else "2.4 GHz",
                            "radio_type": "802.11ac",
                            "rx_rate_mbps": 433.3,
                            "tx_rate_mbps": 433.3,
                            "adapter": "Linux Wireless NIC",
                            "is_simulated": False,
                            "raw_output": output.strip(),
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
            except Exception:
                pass

        elif sys.platform == "darwin":
            try:
                airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
                proc = subprocess.run([airport_path, "-I"], capture_output=True, text=True, timeout=3)
                output = proc.stdout or ""
                if "SSID" in output:
                    agrCtlRSSI = re.search(r"agrCtlRSSI:\s*(-?\d+)", output)
                    ssid = re.search(r"^\s*SSID:\s*(.+)$", output, re.M)
                    bssid = re.search(r"^\s*BSSID:\s*(.+)$", output, re.M)
                    channel = re.search(r"^\s*channel:\s*(\d+)", output, re.M)
                    rssi_val = float(agrCtlRSSI.group(1)) if agrCtlRSSI else -55.0
                    chan = int(channel.group(1)) if channel else 44
                    return {
                        "status": "connected",
                        "ssid": ssid.group(1).strip() if ssid else "Campus_WLAN",
                        "bssid": bssid.group(1).strip() if bssid else "00:1A:2B:3C:4D:5E",
                        "signal_pct": max(0.0, min(100.0, 2 * (rssi_val + 100))),
                        "rssi_dbm": rssi_val,
                        "channel": chan,
                        "band": "5 GHz" if chan > 14 else "2.4 GHz",
                        "radio_type": "802.11ax",
                        "rx_rate_mbps": 600.0,
                        "tx_rate_mbps": 600.0,
                        "adapter": "macOS Wi-Fi Airport",
                        "is_simulated": False,
                        "raw_output": output.strip(),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            except Exception:
                pass

    # High-fidelity synthetic fallback
    random.seed(int(time.time() * 10) + seed_offset)
    rssi_base = -56.0 + random.uniform(-4.0, 4.0)
    sig_pct = max(10.0, min(100.0, 2.0 * (rssi_base + 100.0)))
    sim_output = (
        "There is 1 interface on the system (SYNTHETIC FALLBACK):\n"
        "    Name                   : Wi-Fi (Simulated)\n"
        "    Description            : Intel(R) Wi-Fi 6 AX201 160MHz (Virtual Driver)\n"
        "    State                  : connected\n"
        f"    SSID                   : GRIET-Campus-WiFi-5G\n"
        "    AP BSSID               : 74:83:c2:41:9b:12\n"
        "    Band                   : 5 GHz\n"
        "    Channel                : 44\n"
        "    Radio type             : 802.11ax\n"
        "    Authentication         : WPA2-Enterprise (802.1X)\n"
        "    Receive rate (Mbps)    : 573.5\n"
        "    Transmit rate (Mbps)   : 573.5\n"
        f"    Signal                 : {int(sig_pct)}%\n"
        f"    Rssi                   : {int(rssi_base)}\n"
        "    Profile                : GRIET-Campus-WiFi-5G\n"
    )
    return {
        "status": "connected (simulated)",
        "ssid": "GRIET-Campus-WiFi-5G",
        "bssid": "74:83:c2:41:9b:12",
        "signal_pct": round(sig_pct, 1),
        "rssi_dbm": round(rssi_base, 1),
        "channel": 44,
        "band": "5 GHz",
        "radio_type": "802.11ax",
        "rx_rate_mbps": 573.5,
        "tx_rate_mbps": 573.5,
        "adapter": "Intel(R) Wi-Fi 6 AX201 (Simulated)",
        "is_simulated": True,
        "raw_output": sim_output,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


def get_ping_metrics(host: str = "8.8.8.8", count: int = 3, force_simulation: bool = False) -> dict:
    """
    Automates ICMP ping routine to default gateway or DNS resolver (e.g. 8.8.8.8).
    Parses RTT latency, Jitter, and Packet Loss %.
    """
    if not force_simulation:
        try:
            if sys.platform.startswith("win"):
                cmd = f"ping -n {count} -w 1000 {host}"
            else:
                cmd = f"ping -c {count} -W 1 {host}"

            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=count * 1.5 + 2,
                errors="ignore"
            )
            raw = proc.stdout or ""

            # Extract individual ping times
            times = [float(t) for t in re.findall(r"time[=<]([\d\.]+)ms", raw, re.I)]
            lost_match = re.search(r"Lost = \d+ \((\d+)% loss\)", raw, re.I) or re.search(r"(\d+)% packet loss", raw, re.I)
            rtt_match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", raw, re.I)

            if times:
                min_rtt = min(times)
                max_rtt = max(times)
                avg_rtt = round(sum(times) / len(times), 1)
                # Compute jitter as sample standard deviation or successive difference
                if len(times) > 1:
                    jitter = round(float(np.std(times)), 2)
                else:
                    jitter = 1.0
                loss_pct = float(lost_match.group(1)) if lost_match else 0.0

                return {
                    "host": host,
                    "packets_sent": count,
                    "packets_received": len(times),
                    "packet_loss_pct": loss_pct,
                    "rtt_min_ms": min_rtt,
                    "rtt_max_ms": max_rtt,
                    "rtt_avg_ms": avg_rtt,
                    "jitter_ms": jitter,
                    "is_simulated": False,
                    "raw_output": raw.strip(),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception:
            pass

    # Synthetic ping fallback
    base_latency = 18.0 + random.uniform(2.0, 8.0)
    jitter = round(random.uniform(1.2, 4.5), 2)
    min_lat = round(max(5.0, base_latency - jitter), 1)
    max_lat = round(base_latency + jitter, 1)
    avg_lat = round((min_lat + max_lat) / 2.0, 1)

    sim_ping_raw = (
        f"Pinging {host} with 32 bytes of data (SYNTHETIC FALLBACK):\n"
        f"Reply from {host}: bytes=32 time={int(min_lat)}ms TTL=117\n"
        f"Reply from {host}: bytes=32 time={int(avg_lat)}ms TTL=117\n"
        f"Reply from {host}: bytes=32 time={int(max_lat)}ms TTL=117\n\n"
        f"Ping statistics for {host}:\n"
        f"    Packets: Sent = {count}, Received = {count}, Lost = 0 (0% loss),\n"
        "Approximate round trip times in milli-seconds:\n"
        f"    Minimum = {int(min_lat)}ms, Maximum = {int(max_lat)}ms, Average = {int(avg_lat)}ms\n"
    )

    return {
        "host": host,
        "packets_sent": count,
        "packets_received": count,
        "packet_loss_pct": 0.0,
        "rtt_min_ms": min_lat,
        "rtt_max_ms": max_lat,
        "rtt_avg_ms": avg_lat,
        "jitter_ms": jitter,
        "is_simulated": True,
        "raw_output": sim_ping_raw,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


def get_cellular_telemetry(
    carrier: str = "Jio 5G",
    tech: str = "5G NSA",
    band: str = "n78 (3500 MHz)",
    manual_rsrp: float = None,
    x: float = None,
    y: float = None,
    floor_w: float = 30.0,
    floor_h: float = 20.0
) -> dict:
    """
    Captures or simulates mobile cellular parameters (RSRP, RSRQ, SINR).
    If (x, y) coordinates are provided, models realistic exterior cellular tower penetration.
    """
    if manual_rsrp is not None:
        rsrp = float(manual_rsrp)
    elif x is not None and y is not None:
        # Exterior cellular base station placed at exterior (x=38m, y=25m)
        # Closer to perimeter/windows -> higher RSRP (-75 dBm)
        # Deep interior room (x=10, y=8) -> heavy building wall penetration loss (-110 dBm)
        tower_x, tower_y = 38.0, 25.0
        dist = math.sqrt((x - tower_x)**2 + (y - tower_y)**2)
        # Log-distance path loss + concrete wall penetration
        indoor_depth = min(x, floor_w - x, y, floor_h - y)
        penetration_loss = (12.0 - min(12.0, indoor_depth * 1.5))  # exterior edge gets less loss
        base_rsrp = -68.0 - (18.0 * math.log10(max(5.0, dist))) - penetration_loss
        rsrp = round(base_rsrp + random.uniform(-2.5, 2.5), 1)
        rsrp = max(-125.0, min(-60.0, rsrp))
    else:
        # Typical campus ambient cellular reading
        rsrp = round(-84.0 + random.uniform(-5.0, 5.0), 1)

    # Correlate RSRQ and SINR with RSRP
    # RSRQ typically ranges from -5 dB to -20 dB
    # SINR ranges from -3 dB to 28 dB
    normalized = (rsrp + 120.0) / 60.0  # 0 (worst) to 1 (best)
    normalized = max(0.0, min(1.0, normalized))
    rsrq = round(-18.0 + (13.0 * normalized) + random.uniform(-1.0, 1.0), 1)
    sinr = round(-2.0 + (26.0 * normalized) + random.uniform(-1.5, 1.5), 1)

    return {
        "carrier": carrier,
        "tech": tech,
        "band": band,
        "rsrp_dbm": rsrp,
        "rsrq_db": rsrq,
        "sinr_db": sinr,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


def generate_campus_seed_dataset(n_samples: int = 40, floor_w: float = 30.0, floor_h: float = 20.0) -> pd.DataFrame:
    """
    Generates a realistic spatial telemetry dataset for the GRIET Campus Block (30m x 20m).
    Features:
    - AP1 (5 GHz) at (8m, 14m) in "CN Lab 1"
    - AP2 (2.4/5 GHz) at (22m, 6m) in "Seminar Hall & Faculty Block"
    - Exterior Cellular Macro Tower at (38m, 25m) broadcasting 5G/4G
    - Realistic wall attenuation and dead-zones
    """
    random.seed(42)
    np.random.seed(42)

    # Campus predefined survey sample points across distinct campus zones
    zones = [
        {"name": "CN Lab 1 (Near AP1)", "x_range": (4, 12), "y_range": (11, 17)},
        {"name": "CN Lab 2 (Adjoining)", "x_range": (2, 10), "y_range": (4, 10)},
        {"name": "Central Corridor", "x_range": (13, 17), "y_range": (2, 18)},
        {"name": "Server & Storage (Shielded)", "x_range": (14, 18), "y_range": (7, 12)},
        {"name": "Seminar Hall (Near AP2)", "x_range": (18, 26), "y_range": (3, 9)},
        {"name": "Faculty Cabins", "x_range": (19, 28), "y_range": (11, 18)},
        {"name": "East Balcony / Outdoor Terrace", "x_range": (26, 30), "y_range": (2, 18)},
        {"name": "West Stairwell & Fire Exit", "x_range": (0, 4), "y_range": (1, 8)},
    ]

    records = []
    
    # Generate balanced samples across all zones
    samples_per_zone = max(3, n_samples // len(zones))
    
    for zone in zones:
        for _ in range(samples_per_zone):
            x = round(random.uniform(zone["x_range"][0], zone["x_range"][1]), 1)
            y = round(random.uniform(zone["y_range"][0], zone["y_range"][1]), 1)
            
            # --- Wi-Fi Modeling ---
            # Distance to AP1 (8, 14) and AP2 (22, 6)
            d_ap1 = math.sqrt((x - 8.0)**2 + (y - 14.0)**2)
            d_ap2 = math.sqrt((x - 22.0)**2 + (y - 6.0)**2)
            
            # Attenuation factors:
            # Wall penetration penalty if crossing central corridor (x between 12 and 18)
            wall_loss_ap1 = 8.0 if x > 16 else 0.0
            wall_loss_ap2 = 8.0 if x < 14 else 0.0
            
            # Server room extra concrete shielding
            if 14 <= x <= 18 and 7 <= y <= 12:
                shield_loss = 22.0  # Server vault blocks both
            elif zone["name"] == "East Balcony / Outdoor Terrace":
                shield_loss = 28.0  # Thick outer concrete wall attenuates indoor APs heavily
            elif zone["name"] == "West Stairwell & Fire Exit":
                shield_loss = 24.0  # Fire escape concrete stairs
            else:
                shield_loss = 0.0
                
            # Log-distance path loss model: RSSI = P0 - 10*n*log10(d) - Obstacles
            rssi_ap1 = -38.0 - (22.0 * math.log10(max(1.0, d_ap1))) - wall_loss_ap1 - shield_loss
            rssi_ap2 = -40.0 - (20.0 * math.log10(max(1.0, d_ap2))) - wall_loss_ap2 - shield_loss
            
            # Mobile device connects to strongest AP
            wifi_rssi = max(rssi_ap1, rssi_ap2) + random.uniform(-2.0, 2.0)
            wifi_rssi = round(max(-95.0, min(-35.0, wifi_rssi)), 1)
            active_ap = "GRIET-AP-Lab1 (5G)" if rssi_ap1 >= rssi_ap2 else "GRIET-AP-Seminar (2.4G/5G)"
            
            # --- Cellular Modeling ---
            # Outdoor tower is at (36, 24).
            # Outdoor terrace and eastern windows have direct line-of-sight (LOS)!
            dist_cell = math.sqrt((x - 36.0)**2 + (y - 24.0)**2)
            
            if zone["name"] == "East Balcony / Outdoor Terrace":
                # Direct outdoor LOS to macro tower
                cell_rsrp = -62.0 - (16.0 * math.log10(max(3.0, dist_cell))) + random.uniform(-2.0, 2.0)
            elif zone["name"] == "West Stairwell & Fire Exit":
                # Has window openings
                cell_rsrp = -74.0 - (18.0 * math.log10(max(3.0, dist_cell))) + random.uniform(-2.0, 2.0)
            elif 14 <= x <= 18 and 7 <= y <= 12:
                # Heavy server core shielding
                cell_rsrp = -112.0 + random.uniform(-4.0, 2.0)
            else:
                # Interior rooms suffer building penetration loss
                dist_from_east_exterior = 30.0 - x
                dist_from_north_exterior = 20.0 - y
                interior_depth = min(dist_from_east_exterior, dist_from_north_exterior, x, y)
                cell_penetration_loss = interior_depth * 2.8
                cell_rsrp = -68.0 - (20.0 * math.log10(max(5.0, dist_cell))) - cell_penetration_loss + random.uniform(-2.0, 2.0)
                
            cell_rsrp = round(max(-122.0, min(-62.0, cell_rsrp)), 1)
            
            cell_op = random.choice(["Jio 5G", "Airtel 5G", "Jio 5G"])
            cell_tech = "5G NSA" if cell_rsrp > -95 else "4G LTE"
            
            # --- Network Performance Metrics (Correlated with Signal) ---
            # When Wi-Fi RSSI is strong (>-65 dBm): Latency low (4-15ms), Loss 0%, Jitter low
            # When Wi-Fi RSSI drops (< -80 dBm): Packet loss spikes, Jitter spikes
            if wifi_rssi > -60:
                lat = round(random.uniform(4.0, 12.0), 1)
                jitter = round(random.uniform(0.5, 2.0), 1)
                loss = 0.0
            elif wifi_rssi > -72:
                lat = round(random.uniform(14.0, 28.0), 1)
                jitter = round(random.uniform(1.8, 4.5), 1)
                loss = round(random.choice([0.0, 0.0, 1.0]), 1)
            elif wifi_rssi > -82:
                lat = round(random.uniform(32.0, 65.0), 1)
                jitter = round(random.uniform(4.0, 12.0), 1)
                loss = round(random.uniform(2.0, 8.0), 1)
            else:  # Severe Wi-Fi Dead zone
                lat = round(random.uniform(75.0, 190.0), 1)
                jitter = round(random.uniform(14.0, 35.0), 1)
                loss = round(random.uniform(12.0, 28.0), 1)
                
            # Composite Network Health Score:
            # Health Score = 100 - (Loss % * 0.5) - (Jitter * 0.3) - (Latency Penalty * 0.2)
            lat_penalty = min(50.0, lat * 0.25)
            health = 100.0 - (loss * 0.5) - (jitter * 0.3) - (lat_penalty * 0.2)
            health = round(max(5.0, min(100.0, health)), 1)
            
            records.append({
                "X": x,
                "Y": y,
                "Zone": zone["name"],
                "WiFi_SSID": active_ap,
                "WiFi_RSSI": wifi_rssi,
                "Cell_Operator": cell_op,
                "Cell_Tech": cell_tech,
                "Cell_RSRP": cell_rsrp,
                "Latency_ms": lat,
                "Jitter_ms": jitter,
                "Packet_Loss_Pct": loss,
                "Health_Score": health
            })

    df = pd.DataFrame(records)
    return df
