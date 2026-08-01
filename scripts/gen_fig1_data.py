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

# Bellman-Ford's verdict: fixed, scale-independent, same number regardless
# of a0. This is the base-case edge with no frictions at all.
BF_EDGE_PCT = 4.738  # from earlier validate.py run (product 1.047379)

capitals = np.round(np.arange(0.05, 6.05, 0.05), 3)

scenarios = {
    "fee_only":        dict(fee=0.01,  impact=0.0,   lot=None),
    "slippage_only":    dict(fee=0.0,   impact=0.005, lot=None),
    "combined":         dict(fee=0.005, impact=0.003, lot=0.01),
}

results = {name: [] for name in scenarios}
for name, params in scenarios.items():
    for a0 in capitals:
        cycle, final = find_arbitrage(market, float(a0), max_k=3, **params)
        if cycle is None:
            profit_pct = None
        else:
            profit_pct = (final - a0) / a0 * 100
        results[name].append(profit_pct)

out = {
    "capitals": capitals.tolist(),
    "bf_edge_pct": BF_EDGE_PCT,
    "results": results,
}
with open(DATA_DIR / "fig1_data.json", "w") as f:
    json.dump(out, f)

for name in scenarios:
    sat_pts = [c for c, p in zip(capitals, results[name]) if p is not None]
    if sat_pts:
        print(f"{name}: sat window ~[{min(sat_pts)}, {max(sat_pts)}]")
    else:
        print(f"{name}: never sat in range")