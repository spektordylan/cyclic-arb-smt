import sys, os, json, time, random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

for path in (str(REPO_ROOT), str(SRC_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from rates import build_market
from bellman_ford import find_negative_cycle
from z3_model import find_arbitrage_cycle


def random_market(n, seed, half_spread=0.0005, mid_range=(0.5, 2.0)):
    rng = random.Random(seed)
    pair_mids = {}
    for i in range(n):
        for j in range(i + 1, n):
            pair_mids[(i, j)] = rng.uniform(*mid_range)
    names = [f"C{i}" for i in range(n)]
    return build_market(names, pair_mids, half_spread)


sizes = [4, 5, 6, 7, 8, 9, 10, 11, 12]
n_trials = 5

bf_times, z3_times = [], []

for n in sizes:
    bf_ts, z3_ts = [], []
    for trial in range(n_trials):
        market = random_market(n, seed=trial * 100 + n)

        t0 = time.time()
        find_negative_cycle(market)
        bf_ts.append(time.time() - t0)

        t0 = time.time()
        find_arbitrage_cycle(market, max_k=n)  # full iterative deepening, worst case
        z3_ts.append(time.time() - t0)

    bf_avg = sum(bf_ts) / len(bf_ts)
    z3_avg = sum(z3_ts) / len(z3_ts)
    bf_times.append(bf_avg)
    z3_times.append(z3_avg)
    print(f"n={n:2d}  BF={bf_avg*1000:8.3f}ms  Z3={z3_avg*1000:10.3f}ms  ratio={z3_avg/max(bf_avg,1e-9):8.1f}x")

with open(DATA_DIR / "fig2_data.json", "w") as f:
    json.dump({"sizes": sizes, "bf_times": bf_times, "z3_times": z3_times}, f)