import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from rates import planted_example, cycle_product
from bellman_ford import find_negative_cycle
from z3_model import find_arbitrage_cycle


def fmt_cycle(market, cycle):
    return " -> ".join(market.names[c] for c in cycle)


def main():
    market = planted_example()

    print("=== Bellman-Ford ===")
    bf_cycle, bf_product = find_negative_cycle(market)
    if bf_cycle is None:
        print("no arbitrage found")
    else:
        print(f"cycle:   {fmt_cycle(market, bf_cycle)}")
        print(f"product: {bf_product:.6f}  (profit: {(bf_product - 1) * 100:.3f}%)")

    print("\n=== Z3 (iterative deepening K=3..n) ===")
    z3_cycle, z3_product = find_arbitrage_cycle(market)
    if z3_cycle is None:
        print("no arbitrage found")
    else:
        print(f"cycle:   {fmt_cycle(market, z3_cycle)}")
        print(f"product: {z3_product:.6f}  (profit: {(z3_product - 1) * 100:.3f}%)")

    print("\n=== Agreement check ===")
    if bf_cycle is None or z3_cycle is None:
        ok = bf_cycle is None and z3_cycle is None
        print("MATCH (both found nothing)" if ok else "MISMATCH")
        return

    bf_p = cycle_product(market, bf_cycle)
    z3_p = cycle_product(market, z3_cycle)
    print(f"Bellman-Ford product recomputed independently: {bf_p:.6f}")
    print(f"Z3 product recomputed independently:            {z3_p:.6f}")

    same_currency_set = set(bf_cycle) == set(z3_cycle)
    both_profitable = bf_p > 1.0 and z3_p > 1.0
    print(f"Same currencies involved: {same_currency_set}")
    print(f"Both profitable:          {both_profitable}")


if __name__ == "__main__":
    main()
