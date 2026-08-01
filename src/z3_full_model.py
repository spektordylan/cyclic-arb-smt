"""
The Z3 model handling all three conditions stacked on top of the base
bid/ask rates, each of which independently breaks Bellman-Ford's
log-additive, fixed-edge-weight assumption in a different way:

  1. Fixed fee per trade (see z3_fee_model.py docstring):
        additive, favors LARGER trades (fee is negligible at scale)

  2. Nonlinear price impact / slippage: the rate you actually get degrades
     as a (linear) function of how much you're trading
         effective_rate = base_rate * (1 - IMPACT * a_t)
     This makes the per-hop transition quadratic in a_t, not just affine.
     Bellman-Ford's edge weights are single fixed numbers; there is no
     way to make an edge weight "depend on how much flow crosses it."
     Slippage favors SMALLER trades (impact is negligible at small size):
        the opposite direction from fees, which is what creates a genuine
        interior sweet-spot window rather than a simple threshold.

  3. Integer lot sizes: you can only end up holding an integer number of
     lots of the destination currency; any fractional remainder from the
     conversion is lost (can't trade a fraction of a lot). This is a floor
     operation whose loss depends on the actual (solved-for) value of a_t,
     encoded via an existential integer m_t with
         m_t * LOT <= raw_output < (m_t + 1) * LOT
     There is no shortest-path analog of "round down to the nearest lot."

None of these three, individually or combined, can be folded into a fixed
per-edge weight, which is the entire structural assumption Bellman-Ford
depends on. Z3 represents all three as ordinary constraints over the same
per-hop transition variables.
"""

from z3 import Solver, Int, Real, RealVal, If, And, Distinct, sat


def rate_lookup(rate_matrix, n, ci, cj):
    expr = RealVal(0)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            expr = If(And(ci == i, cj == j), RealVal(rate_matrix[i][j]), expr)
    return expr


def fee_lookup(fee_vec, n, cj):
    expr = RealVal(0)
    for j in range(n):
        expr = If(cj == j, RealVal(fee_vec[j]), expr)
    return expr


def check_capital(market, a0, fee=0.0, impact=0.0, lot=None, k=3):
    """
    Does a profitable k-hop simple cycle exist starting from exactly a0
    units of some currency, under fee/impact/lot frictions?
    lot=None disables lot rounding (continuous holdings).
    Returns (cycle, final_amount) or (None, None).
    """
    n = market.n
    fee_vec = [fee] * n
    s = Solver()

    c = [Int(f"c_{t}") for t in range(k)]
    a = [Real(f"a_{t}") for t in range(k + 1)]
    for ci in c:
        s.add(ci >= 0, ci < n)
    s.add(Distinct(*c))
    s.add(a[0] == a0)

    m = [Int(f"m_{t}") for t in range(k)] if lot is not None else None

    for t in range(k):
        nxt = c[(t + 1) % k]
        base_rate = rate_lookup(market.rate, n, c[t], nxt)
        eff_rate = base_rate * (1 - impact * a[t])
        fee_t = fee_lookup(fee_vec, n, nxt)
        raw = a[t] * eff_rate - fee_t

        if lot is None:
            s.add(a[t + 1] == raw)
        else:
            mi = m[t]
            s.add(mi >= 0)
            s.add(mi * lot <= raw)
            s.add((mi + 1) * lot > raw)
            s.add(a[t + 1] == mi * lot)
        s.add(a[t + 1] >= 0)

    s.add(a[k] > a[0])

    if s.check() == sat:
        model = s.model()
        path = [model.evaluate(ci).as_long() for ci in c]
        path.append(path[0])
        final = float(model.evaluate(a[k]).as_fraction())
        return path, final
    return None, None


def find_arbitrage(market, a0, fee=0.0, impact=0.0, lot=None, max_k=None):
    """Iterative deepening over cycle length, at a fixed starting capital."""
    n = market.n
    if max_k is None:
        max_k = n
    for k in range(3, max_k + 1):
        cycle, final = check_capital(market, a0, fee, impact, lot, k)
        if cycle is not None:
            return cycle, final
    return None, None
