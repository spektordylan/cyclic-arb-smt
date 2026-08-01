import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUT = REPO_ROOT / "figs"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({"font.size": 11, "figure.dpi": 150})

# ---------------------------------------------------------------------------
# Figure 1: profit vs starting capital, three scenarios
# ---------------------------------------------------------------------------
with open(DATA_DIR / "fig1_data.json") as f:
    d1 = json.load(f)

capitals = np.array(d1["capitals"])
fig, ax = plt.subplots(figsize=(8, 5))

labels = {
    "fee_only": "Fee only",
    "slippage_only": "Slippage only",
    "combined": "Fee + slippage + lots",
}
colors = {"fee_only": "#d95f02", "slippage_only": "#1b9e77", "combined": "#7570b3"}

for name in ["fee_only", "slippage_only", "combined"]:
    profits = d1["results"][name]
    xs = [c for c, p in zip(capitals, profits) if p is not None]
    ys = [p for p in profits if p is not None]
    if xs:
        ax.plot(xs, ys, '--', ms=3, color=colors[name], label=labels[name])

ax.axhline(0, color="gray", lw=0.8)
ax.axhline(d1["bf_edge_pct"], color="black", ls="--", lw=1.3, label="Bellman-Ford")

ax.set_xlabel("Starting capital")
ax.set_ylabel("Profit (%)")
ax.set_title("Profitability depends on trade size")
ax.legend(fontsize=8.5, loc="upper right")
ax.set_ylim(-2, 8)
fig.tight_layout()
fig.savefig(OUT / "fig1_profit_vs_capital.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: solve time scaling
# ---------------------------------------------------------------------------
with open(DATA_DIR / "fig2_data.json") as f:
    d2 = json.load(f)

fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(d2["sizes"], [t * 1000 for t in d2["bf_times"]], "o-", color="#1b9e77", label="Bellman-Ford")
ax.plot(d2["sizes"], [t * 1000 for t in d2["z3_times"]], "o-", color="#d95f02", label="Z3")
ax.set_yscale("log")
ax.set_xlabel("Currencies (n)")
ax.set_ylabel("Solve time (ms)")
ax.set_title("Solve time vs. market size")
ax.legend(fontsize=9)
ax.grid(alpha=0.3, which="both")
fig.tight_layout()
fig.savefig(OUT / "fig2_solve_time_scaling.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 3: capability matrix
# ---------------------------------------------------------------------------
rows = ["Flat rates", "Bid/ask", "Fixed fee", "Slippage", "Lot size", "All combined"]
bf_scores = [1, 1, 0, 0, 0, 0]
z3_scores = [1, 1, 1, 1, 1, 1]

fig, ax = plt.subplots(figsize=(6.5, 4))
data = np.array([bf_scores, z3_scores])
ax.imshow(data, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")

ax.set_xticks(range(len(rows)))
ax.set_xticklabels(rows, rotation=30, ha="right", fontsize=9)
ax.set_yticks([0, 1])
ax.set_yticklabels(["Bellman-Ford", "Z3"], fontsize=10)

for r in range(2):
    for c in range(len(rows)):
        val = data[r, c]
        ax.text(c, r, "yes" if val else "no", ha="center", va="center", fontsize=9,
                color="black" if val else "white")

ax.set_title("Conditions handled by each method")
fig.tight_layout()
fig.savefig(OUT / "fig3_capability_matrix.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 4: standalone sweet-spot figure -- Z3 (all 3 conditions) vs BF, alone
# ---------------------------------------------------------------------------
fig4_path = DATA_DIR / "fig4_data.json"
if fig4_path.exists():
    with open(fig4_path) as f:
        d4 = json.load(f)
else:
    print(f"Skipping fig4: {fig4_path} not found")
    plt.close("all")
    print("done")
    raise SystemExit(0)

caps = np.array(d4["capitals"])
profs = d4["profits"]
xs = np.array([c for c, p in zip(caps, profs) if p is not None])
ys = np.array([p for p in profs if p is not None])

# light smoothing so the lot-rounding sawtooth doesn't obscure the shape
def smooth(y, window=9):
    kernel = np.ones(window) / window
    return np.convolve(y, kernel, mode="same")

ys_smooth = smooth(ys) if len(ys) > 9 else ys

fig, ax = plt.subplots(figsize=(7.5, 4.5))
ax.plot(xs, ys_smooth, color="#7570b3", lw=2.2, label="Z3 (fee + slippage + lots)")
ax.axhline(d4["bf_edge_pct"], color="black", ls="--", lw=1.5, label="Bellman-Ford")
ax.axhline(0, color="gray", lw=0.8)

ax.set_xlabel("Starting capital")
ax.set_ylabel("Profit (%)")
ax.set_title("Adaptable Z3 model vs. fixed Bellman-Ford")
ax.legend(fontsize=9.5)
ax.set_ylim(-1, 6)
fig.tight_layout()
fig.savefig(OUT / "fig4_adaptability_comparison.png")
plt.close(fig)

print("done")