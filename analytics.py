"""
AirData Inspector: Spatial Analytics & Multi-Spectrum Engine
Implements Inverse Distance Weighting (IDW) spatial interpolation,
SciPy griddata fallback, Composite Network Health Score, and the
Flagship Unified Optimal Coverage Overlay logic.
"""

import sys
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
import seaborn as sns

# Safe SciPy griddata import with graceful pure-NumPy fallback
HAS_SCIPY_GRIDDATA = False
try:
    from scipy.interpolate import griddata
    HAS_SCIPY_GRIDDATA = True
except Exception:
    HAS_SCIPY_GRIDDATA = False


def compute_health_score(loss_pct: float, jitter_ms: float, latency_ms: float) -> float:
    """
    Computes Composite Network Health Score (0 to 100):
    Health Score = 100 - (Loss% * 0.5) - (Jitter * 0.3) - (Latency Penalty * 0.2)
    where Latency Penalty is scaled to prevent negative outliers.
    """
    lat_penalty = min(50.0, latency_ms * 0.25)
    score = 100.0 - (loss_pct * 0.5) - (jitter_ms * 0.3) - (lat_penalty * 0.2)
    return round(float(np.clip(score, 0.0, 100.0)), 1)


def inverse_distance_weighting(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    values: np.ndarray,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    power: float = 2.0,
    eps: float = 1e-5
) -> np.ndarray:
    """
    Calculates 2D Inverse Distance Weighting (IDW) spatial interpolation:
    Z(s) = sum(w_i * z_i) / sum(w_i) where w_i = 1 / (d(s, s_i) ** power)
    Fully vectorized with pure NumPy for rapid multi-spectrum meshgrid processing.
    """
    x_coords = np.asarray(x_coords, dtype=float)
    y_coords = np.asarray(y_coords, dtype=float)
    values = np.asarray(values, dtype=float)

    # Flatten meshgrid for vectorized pairwise distance calculation
    gx_flat = grid_x.ravel()
    gy_flat = grid_y.ravel()

    # dx, dy shapes: (N_grid, N_points)
    dx = gx_flat[:, np.newaxis] - x_coords[np.newaxis, :]
    dy = gy_flat[:, np.newaxis] - y_coords[np.newaxis, :]
    dists = np.sqrt(dx**2 + dy**2)

    # Check for exact matches to avoid division by zero
    exact_match = dists < eps
    weights = 1.0 / (np.maximum(dists, eps) ** power)

    # Where an exact match occurs, assign weight 1 to that point and 0 to others
    row_has_exact = np.any(exact_match, axis=1)
    if np.any(row_has_exact):
        weights[row_has_exact] = exact_match[row_has_exact].astype(float)

    weights_sum = np.sum(weights, axis=1, keepdims=True)
    interpolated_flat = np.sum(weights * values[np.newaxis, :], axis=1) / weights_sum.ravel()

    return interpolated_flat.reshape(grid_x.shape)


def interpolate_spatial_grid(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    values: np.ndarray,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    method: str = "idw",
    idw_power: float = 2.0
) -> np.ndarray:
    """
    Spatial interpolation wrapper supporting IDW and SciPy griddata methods.
    Automatically falls back to IDW if SciPy griddata DLL is unavailable.
    """
    if method == "idw" or not HAS_SCIPY_GRIDDATA:
        return inverse_distance_weighting(x_coords, y_coords, values, grid_x, grid_y, power=idw_power)
    
    try:
        points = np.column_stack((x_coords, y_coords))
        grid_z = griddata(points, values, (grid_x, grid_y), method=method)
        if np.isnan(grid_z).any():
            grid_z_near = griddata(points, values, (grid_x, grid_y), method="nearest")
            grid_z = np.where(np.isnan(grid_z), grid_z_near, grid_z)
        return grid_z
    except Exception:
        return inverse_distance_weighting(x_coords, y_coords, values, grid_x, grid_y, power=idw_power)


def normalize_signal_quality(wifi_rssi: np.ndarray, cell_rsrp: np.ndarray):
    """
    Normalizes Wi-Fi RSSI (dBm) and Cellular RSRP (dBm) into comparable [0, 100] Quality Indexes.
    - Wi-Fi Range: -95 dBm (0 Quality) to -40 dBm (100 Quality)
    - Cellular Range: -115 dBm (0 Quality) to -65 dBm (100 Quality)
    """
    q_wifi = np.clip((wifi_rssi - (-95.0)) / ((-40.0) - (-95.0)) * 100.0, 0.0, 100.0)
    q_cell = np.clip((cell_rsrp - (-115.0)) / ((-65.0) - (-115.0)) * 100.0, 0.0, 100.0)
    return q_wifi, q_cell


def compute_optimal_coverage_overlay(
    grid_wifi_rssi: np.ndarray,
    grid_cell_rsrp: np.ndarray,
    delta_threshold: float = 8.0,
    dead_zone_cutoff_wifi: float = -82.0,
    dead_zone_cutoff_cell: float = -108.0
):
    """
    Evaluates Wi-Fi vs Cellular performance across every grid coordinate (X, Y).
    Generates categorical decision matrix:
      0: Dual Dead Zone (Both Wi-Fi & Cellular severely degraded)
      1: Cellular Dominant (Mobile data significantly superior)
      2: Balanced Dual-Coverage (Both provide solid signal)
      3: Wi-Fi Dominant (Campus Wi-Fi significantly superior)
    """
    q_wifi, q_cell = normalize_signal_quality(grid_wifi_rssi, grid_cell_rsrp)
    delta_q = q_wifi - q_cell  # Positive -> Wi-Fi wins; Negative -> Cellular wins

    decision_map = np.zeros_like(delta_q, dtype=int)

    # 1. Wi-Fi Dominant
    wifi_dominant = (delta_q >= delta_threshold) & (grid_wifi_rssi > dead_zone_cutoff_wifi)
    decision_map[wifi_dominant] = 3

    # 2. Cellular Dominant
    cell_dominant = (delta_q <= -delta_threshold) & (grid_cell_rsrp > dead_zone_cutoff_cell)
    decision_map[cell_dominant] = 1

    # 3. Balanced Dual-Coverage
    balanced = (np.abs(delta_q) < delta_threshold) & (grid_wifi_rssi > dead_zone_cutoff_wifi) & (grid_cell_rsrp > dead_zone_cutoff_cell)
    decision_map[balanced] = 2

    # 4. Dual Dead Zone
    dual_dead = (grid_wifi_rssi <= dead_zone_cutoff_wifi) & (grid_cell_rsrp <= dead_zone_cutoff_cell)
    decision_map[dual_dead] = 0

    # Calculate coverage area statistics (% of floor area)
    total_cells = decision_map.size
    stats = {
        "wifi_dominant_pct": round(float(np.sum(decision_map == 3) / total_cells * 100.0), 1),
        "cellular_dominant_pct": round(float(np.sum(decision_map == 1) / total_cells * 100.0), 1),
        "balanced_coverage_pct": round(float(np.sum(decision_map == 2) / total_cells * 100.0), 1),
        "dual_dead_zone_pct": round(float(np.sum(decision_map == 0) / total_cells * 100.0), 1),
        "avg_wifi_rssi": round(float(np.mean(grid_wifi_rssi)), 1),
        "avg_cell_rsrp": round(float(np.mean(grid_cell_rsrp)), 1),
    }

    return decision_map, delta_q, stats


def draw_campus_floorplan(ax, floor_w: float = 30.0, floor_h: float = 20.0, show_labels: bool = True):
    """
    Renders architectural campus floor layout outlines and labels over spatial heatmaps.
    Floor dimensions: 30m x 20m (GRIET Computer Networks & IoT Department).
    """
    # Outer floor perimeter
    ax.add_patch(patches.Rectangle((0, 0), floor_w, floor_h, fill=False, edgecolor="#334155", linewidth=2.0, linestyle="-"))

    # Architectural partitions:
    # 1. CN Lab 1 (Top-Left)
    ax.add_patch(patches.Rectangle((0, 10), 14, 10, fill=False, edgecolor="#64748b", linewidth=1.5, linestyle="--"))
    # 2. CN Lab 2 (Bottom-Left)
    ax.add_patch(patches.Rectangle((0, 0), 14, 10, fill=False, edgecolor="#64748b", linewidth=1.5, linestyle="--"))
    # 3. Central Corridor (Vertical spine)
    ax.add_patch(patches.Rectangle((14, 0), 4, 20, fill=False, edgecolor="#94a3b8", linewidth=1.2, linestyle=":"))
    # 4. Server & Core Room (Shielded Vault in corridor)
    ax.add_patch(patches.Rectangle((14, 7), 4, 6, fill=True, facecolor="#475569", alpha=0.25, edgecolor="#ef4444", linewidth=1.5))
    # 5. Faculty Cabins (Top-Right)
    ax.add_patch(patches.Rectangle((18, 10), 12, 10, fill=False, edgecolor="#64748b", linewidth=1.5, linestyle="--"))
    # 6. Seminar & IoT Lab (Bottom-Right)
    ax.add_patch(patches.Rectangle((18, 0), 12, 10, fill=False, edgecolor="#64748b", linewidth=1.5, linestyle="--"))

    if show_labels:
        font_kw = dict(fontsize=8.5, color="#0f172a", weight="bold", ha="center", va="center")
        ax.text(7, 18.5, "CN Lab 1", bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff", alpha=0.85, edgecolor="#cbd5e1"), **font_kw)
        ax.text(7, 1.5, "CN Lab 2", bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff", alpha=0.85, edgecolor="#cbd5e1"), **font_kw)
        ax.text(16, 10, "Server\nRoom", bbox=dict(boxstyle="round,pad=0.2", facecolor="#fee2e2", alpha=0.9, edgecolor="#ef4444"), fontsize=7, color="#991b1b", ha="center", va="center", weight="bold")
        ax.text(24, 18.5, "Faculty Cabins", bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff", alpha=0.85, edgecolor="#cbd5e1"), **font_kw)
        ax.text(24, 1.5, "Seminar Hall", bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff", alpha=0.85, edgecolor="#cbd5e1"), **font_kw)
        ax.text(16, 18.8, "Corridor", fontsize=7.5, color="#475569", ha="center", weight="semibold")

    # Mark Wi-Fi Access Points (AP1 & AP2)
    ax.scatter([8], [14], s=170, color="#2563eb", edgecolors="#ffffff", linewidth=2.0, zorder=10, marker="^", label="Wi-Fi AP1 (5 GHz)")
    ax.scatter([22], [6], s=170, color="#0284c7", edgecolors="#ffffff", linewidth=2.0, zorder=10, marker="^", label="Wi-Fi AP2 (2.4/5 GHz)")

    # Cellular Tower Direction indicator (Exterior East/North)
    ax.annotate(
        "Cellular Macro Tower (5G/4G)\n[Outdoor LOS]",
        xy=(29.5, 19.2),
        xytext=(19.5, 21.6),
        arrowprops=dict(facecolor="#d97706", edgecolor="#ffffff", shrink=0.05, width=1.5, headwidth=6),
        fontsize=7.5,
        color="#b45309",
        weight="bold",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#fef3c7", edgecolor="#f59e0b", alpha=0.95)
    )


def generate_side_by_side_heatmap_figure(
    df: pd.DataFrame,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    grid_wifi: np.ndarray,
    grid_cell: np.ndarray,
    floor_w: float = 30.0,
    floor_h: float = 20.0
) -> plt.Figure:
    """
    Renders side-by-side high-contrast spatial heatmaps for Wi-Fi RSSI vs Cellular RSRP.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5), sharey=True)
    plt.subplots_adjust(wspace=0.12, top=0.88, bottom=0.14)

    wifi_cmap = "RdYlGn"
    cell_cmap = "Spectral"

    # --- Plot 1: Wi-Fi RSSI Heatmap ---
    c1 = ax1.contourf(grid_x, grid_y, grid_wifi, levels=25, cmap=wifi_cmap, vmin=-95, vmax=-35, alpha=0.88)
    cb1 = fig.colorbar(c1, ax=ax1, orientation="horizontal", pad=0.12, shrink=0.85)
    cb1.set_label("Wi-Fi RSSI (dBm)", fontsize=9.5, weight="bold")
    ax1.contour(grid_x, grid_y, grid_wifi, levels=[-82], colors=["#dc2626"], linewidths=2.2, linestyles="--")
    
    # Overlay survey points
    ax1.scatter(df["X"], df["Y"], c=df["WiFi_RSSI"], cmap=wifi_cmap, vmin=-95, vmax=-35, edgecolors="#0f172a", s=40, linewidth=1, zorder=8)
    draw_campus_floorplan(ax1, floor_w, floor_h)
    ax1.set_title("Wi-Fi (5 GHz / 2.4 GHz) Spatial RSSI Distribution", fontsize=11, weight="bold", pad=10)
    ax1.set_xlabel("Floor X Coordinate (meters)", fontsize=9)
    ax1.set_ylabel("Floor Y Coordinate (meters)", fontsize=9)
    ax1.set_xlim(-0.5, floor_w + 0.5)
    ax1.set_ylim(-0.5, floor_h + 2.5)
    ax1.legend(loc="lower left", fontsize=7.5, framealpha=0.92)

    # --- Plot 2: Cellular RSRP Heatmap ---
    c2 = ax2.contourf(grid_x, grid_y, grid_cell, levels=25, cmap=cell_cmap, vmin=-120, vmax=-65, alpha=0.88)
    cb2 = fig.colorbar(c2, ax=ax2, orientation="horizontal", pad=0.12, shrink=0.85)
    cb2.set_label("Cellular RSRP (dBm)", fontsize=9.5, weight="bold")
    ax2.contour(grid_x, grid_y, grid_cell, levels=[-105], colors=["#991b1b"], linewidths=2.2, linestyles="--")

    # Overlay survey points
    ax2.scatter(df["X"], df["Y"], c=df["Cell_RSRP"], cmap=cell_cmap, vmin=-120, vmax=-65, edgecolors="#0f172a", s=40, linewidth=1, zorder=8)
    draw_campus_floorplan(ax2, floor_w, floor_h)
    ax2.set_title("Mobile Cellular (5G / 4G LTE) Spatial RSRP Distribution", fontsize=11, weight="bold", pad=10)
    ax2.set_xlabel("Floor X Coordinate (meters)", fontsize=9)
    ax2.set_xlim(-0.5, floor_w + 0.5)
    ax2.set_ylim(-0.5, floor_h + 2.5)

    return fig


def generate_optimal_coverage_overlay_figure(
    df: pd.DataFrame,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    decision_map: np.ndarray,
    delta_q: np.ndarray,
    stats: dict,
    floor_w: float = 30.0,
    floor_h: float = 20.0
) -> plt.Figure:
    """
    Renders the flagship UNIFIED OPTIMAL COVERAGE OVERLAY MAP.
    Discrete color classification:
    - Wi-Fi Dominant (Green)
    - Cellular Dominant (Amber/Orange)
    - Balanced Dual-Coverage (Cyan/Teal)
    - Dual Dead Zone (Crimson Red)
    """
    fig, ax = plt.subplots(figsize=(10.5, 7.0))
    plt.subplots_adjust(top=0.91, bottom=0.10)

    # Colormap matching categories: 0=Dead, 1=Cell, 2=Balanced, 3=WiFi
    custom_cmap = ListedColormap(["#ef4444", "#f59e0b", "#06b6d4", "#10b981"])
    
    overlay = ax.imshow(
        decision_map,
        extent=(0, floor_w, 0, floor_h),
        origin="lower",
        cmap=custom_cmap,
        alpha=0.76,
        aspect="auto",
        vmin=-0.5,
        vmax=3.5,
        interpolation="bilinear"
    )

    # Draw Handover Boundary Line (where delta_q == 0)
    cs = ax.contour(grid_x, grid_y, delta_q, levels=[0.0], colors=["#1e1b4b"], linewidths=2.5, linestyles="-.")
    ax.clabel(cs, inline=True, fmt="Handover (ΔQ=0)", fontsize=8, colors="#1e1b4b")

    draw_campus_floorplan(ax, floor_w, floor_h)

    # Plot sample coordinate markers
    ax.scatter(df["X"], df["Y"], s=50, facecolors="#ffffff", edgecolors="#0f172a", linewidth=1.5, zorder=9, label="Survey Waypoints")

    # Legend handles for decision zones
    legend_elements = [
        patches.Patch(facecolor="#10b981", edgecolor="#059669", label=f"Wi-Fi Optimal ({stats['wifi_dominant_pct']}%)"),
        patches.Patch(facecolor="#f59e0b", edgecolor="#d97706", label=f"Cellular Optimal ({stats['cellular_dominant_pct']}%)"),
        patches.Patch(facecolor="#06b6d4", edgecolor="#0891b2", label=f"Balanced Dual-Coverage ({stats['balanced_coverage_pct']}%)"),
        patches.Patch(facecolor="#ef4444", edgecolor="#dc2626", label=f"Dual Dead Zone ({stats['dual_dead_zone_pct']}%)"),
        plt.Line2D([0], [0], color="#1e1b4b", lw=2, linestyle="-.", label="Handover Boundary (Delta Q = 0)")
    ]
    ax.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(0.99, 0.98), fontsize=8.5, framealpha=0.94, facecolor="#ffffff")

    ax.set_title(
        "UNIFIED OPTIMAL COVERAGE OVERLAY MAP\n"
        "Dynamic Decision Surface: Wi-Fi vs Mobile Cellular Signal Superiority",
        fontsize=11.5,
        weight="bold",
        pad=12
    )
    ax.set_xlabel("Floor X Dimension (meters)", fontsize=9.5)
    ax.set_ylabel("Floor Y Dimension (meters)", fontsize=9.5)
    ax.set_xlim(-0.5, floor_w + 0.5)
    ax.set_ylim(-0.5, floor_h + 2.5)

    return fig


def generate_dead_zone_identifier_figure(
    df: pd.DataFrame,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    grid_wifi: np.ndarray,
    grid_cell: np.ndarray,
    floor_w: float = 30.0,
    floor_h: float = 20.0
) -> plt.Figure:
    """
    Renders dedicated Dead-Zone Identifier Map highlighting coverage dropouts.
    """
    fig, ax = plt.subplots(figsize=(9.5, 6.2))

    wifi_dead = grid_wifi < -82.0
    cell_dead = grid_cell < -108.0

    q_w, q_c = normalize_signal_quality(grid_wifi, grid_cell)
    combined_health = np.maximum(q_w, q_c)
    
    bg = ax.contourf(grid_x, grid_y, combined_health, levels=20, cmap="PuBuGn", alpha=0.55, vmin=0, vmax=100)
    cb = fig.colorbar(bg, ax=ax, orientation="vertical", shrink=0.85, pad=0.03)
    cb.set_label("Effective Multi-Spectrum Signal Quality (0 - 100)", fontsize=8.5, weight="bold")

    # Hatching for Wi-Fi Dead Zones
    ax.contourf(grid_x, grid_y, wifi_dead.astype(int), levels=[0.5, 1.5], colors=["none"], hatches=["//"], alpha=0)
    ax.contour(grid_x, grid_y, wifi_dead.astype(int), levels=[0.5], colors=["#dc2626"], linewidths=2.0)

    # Hatching for Cellular Dead Zones
    ax.contourf(grid_x, grid_y, cell_dead.astype(int), levels=[0.5, 1.5], colors=["none"], hatches=["\\\\"], alpha=0)
    ax.contour(grid_x, grid_y, cell_dead.astype(int), levels=[0.5], colors=["#d97706"], linewidths=2.0)

    draw_campus_floorplan(ax, floor_w, floor_h)

    hatch_legend = [
        patches.Patch(facecolor="none", edgecolor="#dc2626", hatch="//", label="Wi-Fi Dead Zone (RSSI < -82 dBm)"),
        patches.Patch(facecolor="none", edgecolor="#d97706", hatch="\\\\", label="Cellular Dropout (RSRP < -108 dBm)"),
        patches.Patch(facecolor="#ef4444", alpha=0.6, label="Critical Dual Blindspot (AP Addition Advised)")
    ]
    ax.legend(handles=hatch_legend, loc="upper right", fontsize=8, framealpha=0.92)

    ax.set_title("Spectrum Dead-Zone & Attenuation Vulnerability Map", fontsize=11, weight="bold", pad=12)
    ax.set_xlabel("Floor X Coordinate (meters)", fontsize=9)
    ax.set_ylabel("Floor Y Coordinate (meters)", fontsize=9)
    ax.set_xlim(-0.5, floor_w + 0.5)
    ax.set_ylim(-0.5, floor_h + 2.5)

    return fig


def generate_correlation_plots(df: pd.DataFrame) -> plt.Figure:
    """
    Renders 4-quadrant correlation graphs illustrating performance decay
    when RSSI/RSRP drop below threshold levels.
    """
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    plt.subplots_adjust(wspace=0.25, hspace=0.32, top=0.92, bottom=0.08)

    # 1. Wi-Fi RSSI vs Packet Loss %
    ax1 = axes[0, 0]
    sns.regplot(
        data=df, x="WiFi_RSSI", y="Packet_Loss_Pct",
        ax=ax1, color="#ef4444", scatter_kws={"alpha": 0.7, "s": 45}, line_kws={"color": "#991b1b", "linewidth": 2}
    )
    ax1.axvline(-80.0, color="#dc2626", linestyle="--", linewidth=1.5, label="Dead-Zone Cliff (-80 dBm)")
    ax1.set_title("Wi-Fi RSSI vs Packet Loss (%) Spikes", fontsize=10.5, weight="bold")
    ax1.set_xlabel("Wi-Fi RSSI (dBm)", fontsize=9)
    ax1.set_ylabel("ICMP Packet Loss (%)", fontsize=9)
    ax1.legend(fontsize=8, loc="upper left")
    ax1.grid(True, linestyle=":", alpha=0.6)

    # 2. Wi-Fi RSSI vs Latency & Jitter
    ax2 = axes[0, 1]
    sns.regplot(
        data=df, x="WiFi_RSSI", y="Latency_ms",
        ax=ax2, color="#2563eb", scatter_kws={"alpha": 0.7, "s": 45}, line_kws={"color": "#1d4ed8", "linewidth": 2}, label="Latency (ms)"
    )
    ax2.set_title("Signal RSSI vs Round-Trip Time (RTT Latency)", fontsize=10.5, weight="bold")
    ax2.set_xlabel("Wi-Fi RSSI (dBm)", fontsize=9)
    ax2.set_ylabel("Round-Trip Time (ms)", fontsize=9)
    ax2.grid(True, linestyle=":", alpha=0.6)

    # 3. Wi-Fi RSSI vs Cellular RSRP (Multi-Spectrum Parity)
    ax3 = axes[1, 0]
    sns.scatterplot(
        data=df, x="WiFi_RSSI", y="Cell_RSRP", hue="Zone",
        palette="tab10", s=65, ax=ax3, alpha=0.85
    )
    ax3.set_title("Multi-Spectrum Balance: Wi-Fi RSSI vs Cellular RSRP", fontsize=10.5, weight="bold")
    ax3.set_xlabel("Wi-Fi RSSI (dBm)", fontsize=9)
    ax3.set_ylabel("Cellular RSRP (dBm)", fontsize=9)
    ax3.legend(fontsize=7, bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0)
    ax3.grid(True, linestyle=":", alpha=0.6)

    # 4. Composite Health Score Distribution across Zones
    ax4 = axes[1, 1]
    sns.boxplot(
        data=df, x="Zone", y="Health_Score",
        palette="viridis", ax=ax4, hue="Zone", legend=False
    )
    ax4.set_title("Composite Health Score by Campus Zone", fontsize=10.5, weight="bold")
    ax4.set_xlabel("Campus Zone", fontsize=9)
    ax4.set_ylabel("Health Score (0-100)", fontsize=9)
    ax4.tick_params(axis="x", rotation=35, labelsize=7.5)
    ax4.grid(True, linestyle=":", alpha=0.6)

    fig.suptitle("Cross-Spectrum Telemetry Correlation & QoS Regression Suite", fontsize=12.5, weight="bold")
    return fig
