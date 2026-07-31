import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from tabulate import tabulate
import pandas as pd

from rates import planted_example
from bellman_ford import find_negative_cycle
from z3_fee_model import find_arbitrage_cycle_with_fee

FEE = 0.01


def fmt(market, cycle):
    return " -> ".join(market.names[c] for c in cycle)


def main():
    market = planted_example()
    fee_vec = [FEE] * market.n

    bf_cycle, bf_product = find_negative_cycle(market)
    bf_result = f"{(bf_product - 1) * 100:.3f}% ({fmt(market, bf_cycle)})"

    rows = []

    # Fixed starting capital
    for a0 in (0.30, 2.00):
        cycle, a0v, akv = find_arbitrage_cycle_with_fee(
            market, fee_vec, a0=a0
        )

        if cycle is None:
            z3 = "UNSAT"
        else:
            profit = (akv - a0v) / a0v * 100
            z3 = f"SAT: {profit:.3f}% ({fmt(market, cycle)})"

        rows.append({
            "Capital regime": f"a0 = {a0:.2f}",
            "Bellman-Ford (fee-blind)": bf_result,
            "Fee-aware Z3": z3,
        })

    # Variable starting capital
    for lo, hi in [(0.01, 0.45), (0.01, 10.0)]:
        cycle, a0v, akv = find_arbitrage_cycle_with_fee(
            market, fee_vec, a0_bounds=(lo, hi)
        )

        if cycle is None:
            z3 = "UNSAT"
        else:
            profit = (akv - a0v) / a0v * 100
            z3 = f"SAT: a0 = {a0v:.2f}, {profit:.3f}% ({fmt(market, cycle)})"

        rows.append({
            "Capital regime": f"a0 ∈ [{lo:.2f}, {hi:.2f}]",
            "Bellman-Ford (fee-blind)": bf_result,
            "Fee-aware Z3": z3,
        })

    df = pd.DataFrame(rows)

    print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))


if __name__ == "__main__":
    main()