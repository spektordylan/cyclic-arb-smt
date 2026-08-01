import sys, os, json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

for path in (str(REPO_ROOT), str(SRC_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import numpy as np

from rates import planted_example
from z3_full_model import find_arbitrage

market = planted_example()

FEE, IMPACT, LOT = 0.005, 0.003, 0.001
BF_EDGE_PCT = 4.738

capitals = np.round(np.arange(0.1, 7.0, 0.05), 3)
profits = []
for a0 in capitals:
    cycle, final = find_arbitrage(market, float(a0), fee=FEE, impact=IMPACT, lot=LOT, max_k=3)
    profits.append(None if cycle is None else (final - a0) / a0 * 100)

with open(DATA_DIR / "fig4_data.json", "w") as f:
    json.dump({"capitals": capitals.tolist(), "profits": profits, "bf_edge_pct": BF_EDGE_PCT}, f)

sat_pts = [c for c, p in zip(capitals, profits) if p is not None]
if sat_pts:
    print(f"sat window: [{min(sat_pts)}, {max(sat_pts)}]")
else:
    print("sat window: empty")
 