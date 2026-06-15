import csv
import collections
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
import numpy as np
from scipy.interpolate import griddata

CSV_PATH = "./performance/inner_insert/results/trials.csv"
OUT      = "./performance/inner_insert/results"

# ── theme ──────────────────────────────────────────────────────────────────
BG        = "#0D1117"
AX_BG     = "#161B22"
GRID_COL  = "#21262D"
TEXT_COL  = "#C9D1D9"
SPINE_COL = "#30363D"
FONT      = "monospace"

METHOD_STYLE = {
    "unbuffered": {"color": "#58A6FF", "marker": "o", "ls": "-"},
    "buffered":   {"color": "#3FB950", "marker": "s", "ls": "-"},
    "fallocate":  {"color": "#F0883E", "marker": "^", "ls": "-"},
    "smartfiles": {"color": "#BC8CFF", "marker": "D", "ls": "-"},
}
METHOD_LABEL = {
    "unbuffered": "naive file io (unbuffered)",
    "buffered":   "naive file io (buffered)",
    "fallocate":  "fallocate",
    "smartfiles": "smartfiles",
}
HEATMAP_CMAP = "magma"


# ── load ───────────────────────────────────────────────────────────────────
def load_data(path):
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            m = row["Method"].strip().lower()
            if not m:
                continue
            rows.append({
                "method":     m,
                "time_ms":    float(row["Time (ms)"]),
                "file_kib":   float(row["File Size (KiB)"]),
                "offset_kib": float(row["Offset (KiB)"]),
                "insert_kib": float(row["Insert Size (KiB)"]),
                "chunk_kib":  float(row["Chunk Size (KiB)"]),
            })
    return rows


def filter_rows(rows, **eq):
    out = rows
    for k, v in eq.items():
        out = [r for r in out if r[k] == v]
    return out


def mean_by(rows, x_key, **eq):
    filtered = filter_rows(rows, **eq)
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in filtered:
        acc[r["method"]][r[x_key]].append(r["time_ms"])
    return {m: {x: np.mean(ts) for x, ts in xd.items()}
            for m, xd in acc.items()}


def heatmap_df(rows, method, x_key, y_key, **eq):
    filtered = filter_rows(rows, method=method, **eq)
    acc = collections.defaultdict(list)
    for r in filtered:
        acc[(r[x_key], r[y_key])].append(r["time_ms"])
    if not acc:
        return np.array([]), np.array([]), np.array([])
    xs, ys, zs = zip(*[(x, y, np.mean(ts)) for (x, y), ts in acc.items()])
    return np.array(xs), np.array(ys), np.array(zs)


# ── styling helpers ────────────────────────────────────────────────────────
def apply_base(fig, axes):
    fig.patch.set_facecolor(BG)
    for ax in (axes if hasattr(axes, "__iter__") else [axes]):
        ax.set_facecolor(AX_BG)
        for sp in ax.spines.values():
            sp.set_edgecolor(SPINE_COL)
        ax.tick_params(colors=TEXT_COL, labelsize=9, which="both", length=3, width=0.6)
        ax.xaxis.label.set_color(TEXT_COL)
        ax.yaxis.label.set_color(TEXT_COL)
        ax.title.set_color(TEXT_COL)


def apply_grid(ax, log_x=False, log_y=False):
    if log_x: ax.set_xscale("log")
    if log_y: ax.set_yscale("log")
    ax.grid(True, which="both", linestyle="--", linewidth=0.35, color=GRID_COL, alpha=1.0)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}"))


def style_legend(ax):
    leg = ax.get_legend()
    if not leg: return
    leg.get_frame().set_facecolor("#1C2128")
    leg.get_frame().set_edgecolor(SPINE_COL)
    for t in leg.get_texts():
        t.set_color(TEXT_COL); t.set_fontsize(9); t.set_fontfamily(FONT)


def save(fig, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"  saved → {path}")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# P1  Time vs File Size  (linear  +  log)
# ══════════════════════════════════════════════════════════════════════════════
def plot_p1(rows, ins_fixed, off_fixed, methods, log_scale):
    data = mean_by(rows, "file_kib", insert_kib=ins_fixed, offset_kib=off_fixed)

    fig, ax = plt.subplots(figsize=(10, 5))
    apply_base(fig, ax)

    for m in methods:
        s   = METHOD_STYLE[m]
        pts = data.get(m, {})
        if log_scale:
            pts = {x: v for x, v in pts.items() if v > 0}
        xs = sorted(pts); ys = [pts[x] for x in xs]
        if xs:
            ax.plot(xs, ys, label=METHOD_LABEL.get(m, m),
                    color=s["color"], marker=s["marker"], ls=s["ls"],
                    linewidth=1.8, markersize=6, markeredgewidth=0, alpha=0.93, zorder=3)

    apply_grid(ax, log_x=log_scale, log_y=log_scale)
    ax.set_xlabel("File Size (KiB)",   fontsize=10, labelpad=8,  fontfamily=FONT)
    ax.set_ylabel("Time (ms)",         fontsize=10, labelpad=8,  fontfamily=FONT)
    scale_label = "log–log" if log_scale else "linear"
    ax.set_title(
        f"Insertion Time vs File Size  [{scale_label}]\n"
        f"fixed insert = {ins_fixed:g} KiB · fixed offset = {off_fixed:g} KiB · all methods",
        fontsize=11, pad=12, fontfamily=FONT,
    )
    ax.legend(frameon=True, fontsize=9); style_legend(ax)
    fig.tight_layout(pad=1.6)
    suffix = "log" if log_scale else "linear"
    save(fig, os.path.join(OUT, f"p1_time_vs_file_size_{suffix}.png"))


# ══════════════════════════════════════════════════════════════════════════════
# P2  Time vs Insert Size  (linear)
# ══════════════════════════════════════════════════════════════════════════════
def plot_p2(rows, lgf, off_end, methods):
    data = mean_by(rows, "insert_kib", file_kib=lgf, offset_kib=off_end)

    fig, ax = plt.subplots(figsize=(10, 5))
    apply_base(fig, ax)

    for m in methods:
        s   = METHOD_STYLE[m]
        pts = data.get(m, {})
        xs = sorted(pts); ys = [pts[x] for x in xs]
        if xs:
            ax.plot(xs, ys, label=METHOD_LABEL.get(m, m),
                    color=s["color"], marker=s["marker"], ls=s["ls"],
                    linewidth=1.8, markersize=6, markeredgewidth=0, alpha=0.93, zorder=3)

    apply_grid(ax, log_x=False, log_y=False)
    ax.set_xlabel("Insert Size (KiB)", fontsize=10, labelpad=8,  fontfamily=FONT)
    ax.set_ylabel("Time (ms)",         fontsize=10, labelpad=8,  fontfamily=FONT)
    ax.set_title(
        f"Insertion Time vs Insert Size  [linear]\n"
        f"fixed file = {lgf:g} KiB · offset ≈ end of file ({off_end:g} KiB) · all methods",
        fontsize=11, pad=12, fontfamily=FONT,
    )
    ax.legend(frameon=True, fontsize=9); style_legend(ax)
    fig.tight_layout(pad=1.6)
    save(fig, os.path.join(OUT, "p2_time_vs_insert_size_linear.png"))


# ══════════════════════════════════════════════════════════════════════════════
# P5  Heatmap File × Insert Size  (log, shared scale across methods)
# ══════════════════════════════════════════════════════════════════════════════
def plot_p5(rows, off_fixed, methods):
    # Gather data per method
    frames = {m: heatmap_df(rows, m, "file_kib", "insert_kib", offset_kib=off_fixed)
              for m in methods}

    # Shared colour scale
    all_z = []
    for xs, ys, zs in frames.values():
        pos = zs[zs > 0] if len(zs) else np.array([])
        all_z.extend(pos.tolist())
    vmin = min(all_z) if all_z else 1e-3
    vmax = max(all_z) if all_z else 1.0
    norm = mcolors.LogNorm(vmin=max(vmin, 1e-6), vmax=vmax)

    n    = len(methods)
    cols = 2
    rows_n = (n + 1) // 2

    # Extra right margin for the colourbar
    fig, axes = plt.subplots(rows_n, cols,
                             figsize=(14, 5.5 * rows_n),
                             gridspec_kw={"right": 0.88})
    axes_flat = list(np.array(axes).flat)
    apply_base(fig, axes_flat)
    fig.suptitle(
        f"Heatmap: File Size × Insert Size → Insertion Time  [log scale, shared colourbar]\n"
        f"fixed offset = {off_fixed:g} KiB",
        color=TEXT_COL, fontsize=12, fontfamily=FONT, y=1.01,
    )

    last_sc = None
    for i, m in enumerate(methods):
        ax = axes_flat[i]
        xs, ys, zs = frames[m]

        if len(zs) < 3:
            ax.text(0.5, 0.5, "no data", transform=ax.transAxes,
                    ha="center", va="center", color=TEXT_COL, fontfamily=FONT)
        else:
            mask = (xs > 0) & (ys > 0) & (zs > 0)
            xs2, ys2, zs2 = xs[mask], ys[mask], zs[mask]
            if len(zs2) >= 3:
                xi = np.geomspace(xs2.min(), xs2.max(), 90)
                yi = np.geomspace(ys2.min(), ys2.max(), 90)
                XX, YY = np.meshgrid(xi, yi)
                ZZ = griddata((xs2, ys2), zs2, (XX, YY), method="linear")
                ax.pcolormesh(XX, YY, ZZ, cmap=HEATMAP_CMAP, norm=norm,
                              shading="gouraud", zorder=1)
                sc = ax.scatter(xs2, ys2, c=zs2, cmap=HEATMAP_CMAP, norm=norm,
                                s=40, edgecolors="#FFFFFF", linewidths=0.4,
                                zorder=5, alpha=0.85)
                last_sc = sc
                ax.set_xscale("log"); ax.set_yscale("log")

        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.set_xlabel("File Size (KiB)",   fontsize=9, labelpad=6, fontfamily=FONT)
        ax.set_ylabel("Insert Size (KiB)", fontsize=9, labelpad=6, fontfamily=FONT)
        ax.set_title(METHOD_LABEL.get(m, m), fontsize=10, pad=10, fontfamily=FONT)
        ax.grid(True, which="both", linestyle="--", linewidth=0.3,
                color=GRID_COL, alpha=0.5)

    # Hide spare axes
    for j in range(n, rows_n * cols):
        axes_flat[j].set_visible(False)

    # Colourbar pinned to the right, well clear of the subplots
    if last_sc is not None:
        sm = plt.cm.ScalarMappable(cmap=HEATMAP_CMAP, norm=norm)
        sm.set_array([])
        cbar_ax = fig.add_axes([0.91, 0.15, 0.018, 0.70])   # [left, bottom, width, height]
        cb = fig.colorbar(sm, cax=cbar_ax)
        cb.set_label("Time (ms)", color=TEXT_COL, fontsize=10, fontfamily=FONT)
        cb.ax.yaxis.set_tick_params(color=TEXT_COL, labelsize=8)
        plt.setp(cb.ax.yaxis.get_ticklabels(), color=TEXT_COL, fontfamily=FONT)

    fig.tight_layout(pad=1.8, rect=[0, 0, 0.90, 1.0])
    save(fig, os.path.join(OUT, "p5_heatmap_file_x_insert_log.png"))


# ══════════════════════════════════════════════════════════════════════════════
# P6  Bar chart  (log y)
# ══════════════════════════════════════════════════════════════════════════════
def plot_p6(rows, ins_fixed, off_fixed, methods, n_groups=6):
    data = mean_by(rows, "file_kib", insert_kib=ins_fixed, offset_kib=off_fixed)

    all_files   = sorted(set(r["file_kib"] for r in rows))
    # Clamp to unbuffered max so bars stay comparable
    ub_max = max(data.get("unbuffered", {0: 0}).keys(), default=None)
    if ub_max:
        all_files = [f for f in all_files if f <= ub_max]

    idxs   = np.linspace(0, len(all_files) - 1, min(n_groups, len(all_files)), dtype=int)
    chosen = [all_files[i] for i in idxs]

    width = 0.72 / len(methods)
    x     = np.arange(len(chosen))

    fig, ax = plt.subplots(figsize=(12, 5))
    apply_base(fig, ax)
    ax.grid(True, axis="y", linestyle="--", linewidth=0.35, color=GRID_COL, alpha=1.0)
    ax.set_axisbelow(True)

    for i, m in enumerate(methods):
        s      = METHOD_STYLE[m]
        pts    = data.get(m, {})
        ys     = [pts.get(f, np.nan) for f in chosen]
        offset = (i - (len(methods) - 1) / 2) * width
        bars   = ax.bar(x + offset, ys, width * 0.88,
                        label=METHOD_LABEL.get(m, m), color=s["color"],
                        alpha=0.88, zorder=3, linewidth=0)
        for bar, val in zip(bars, ys):
            if not np.isnan(val) and val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() * 1.08,
                        f"{val:.1f}", ha="center", va="bottom",
                        color=TEXT_COL, fontsize=6.5, fontfamily=FONT)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{f:g}" for f in chosen],
                       color=TEXT_COL, fontfamily=FONT, fontsize=9)
    ax.set_xlabel("File Size (KiB)",  fontsize=10, labelpad=8, fontfamily=FONT, color=TEXT_COL)
    ax.set_ylabel("Time (ms)",        fontsize=10, labelpad=8, fontfamily=FONT, color=TEXT_COL)
    ax.set_title(
        f"Insertion Time vs File Size  [log scale]  — buffered, unbuffered & smartfiles\n"
        f"fixed insert = {ins_fixed:g} KiB · fixed offset = {off_fixed:g} KiB · file sizes up to unbuffered max",
        fontsize=11, pad=12, fontfamily=FONT, color=TEXT_COL,
    )
    ax.tick_params(colors=TEXT_COL, labelsize=9)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.legend(frameon=True, fontsize=9); style_legend(ax)
    fig.tight_layout(pad=1.6)
    save(fig, os.path.join(OUT, "p6_bar_time_vs_file_size_log.png"))


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Loading data …")
    rows = load_data(CSV_PATH)
    print(f"  {len(rows)} rows")

    all_inserts = sorted(set(r["insert_kib"] for r in rows))
    all_offsets = sorted(set(r["offset_kib"] for r in rows))
    all_files   = sorted(set(r["file_kib"]   for r in rows))
    all_methods = sorted(set(r["method"]      for r in rows))

    ins_fixed = min(all_inserts, key=lambda x: abs(x - 4.0))
    off_fixed = min(all_offsets, key=lambda x: abs(x - 4.0))
    off_end   = all_offsets[-1]

    # Largest file that has data at off_end
    lgf_candidates = [f for f in reversed(all_files)
                      if len(filter_rows(rows, file_kib=f, offset_kib=off_end)) > 0]
    lgf = lgf_candidates[0] if lgf_candidates else all_files[-1]

    print(f"  ins_fixed={ins_fixed} KiB  off_fixed={off_fixed} KiB  off_end={off_end} KiB  lgf={lgf} KiB")
    print(f"  methods: {all_methods}")

    METHODS_ALL    = ["unbuffered", "buffered", "fallocate", "smartfiles"]
    METHODS_NO_RAW = ["buffered", "fallocate", "smartfiles"]
    METHODS_BAR    = ["unbuffered", "buffered", "smartfiles"]

    print("\nP1 linear …"); plot_p1(rows, ins_fixed, off_fixed, METHODS_ALL, log_scale=False)
    print("P1 log …");    plot_p1(rows, ins_fixed, off_fixed, METHODS_ALL, log_scale=True)
    print("P2 linear …"); plot_p2(rows, lgf, off_end, METHODS_ALL)
    print("P5 log …");    plot_p5(rows, off_fixed, METHODS_NO_RAW)
    print("P6 log …");    plot_p6(rows, ins_fixed, off_fixed, METHODS_BAR)

    print("\n✓  All plots saved.")
