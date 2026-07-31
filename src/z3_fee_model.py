"""
Fee-aware extension. A flat, fixed fee per trade (charged in the destination
currency of that hop) breaks the multiplicative/log-additive structure
Bellman-Ford relies on:

    a_{t+1} = a_t * rate[c_t][c_{t+1}] - fee[c_{t+1}]

This is affine in a_t, not purely multiplicative, so "profitable" no longer
reduces to "product of rates > 1". It depends on the starting capital a_0.
Bellman-Ford has no way to represent this at all: its edge weights
(-log(rate)) are fixed numbers, independent of trade size, by construction.

Two modes here:
  1. Fixed a_0 (a float): check whether a given cycle is profitable at that
     exact starting capital.
  2. a_0 as a free Real variable bounded in [lo, hi]: ask Z3 whether there
     EXISTS a starting capital in that range (and a cycle) that's
     profitable. This is a genuinely joint search Bellman-Ford cannot even
     pose as a question, since it has no notion of capital in its model.
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
    """fee charged, denominated in the destination currency cj."""
    expr = RealVal(0)
    for j in range(n):
        expr = If(cj == j, RealVal(fee_vec[j]), expr)
    return expr


def find_cycle_of_length_with_fee(market, fee_vec, k, a0, a0_bounds=None):
    """
    a0: float -> starting capital fixed to this value.
    a0_bounds: (lo, hi) -> ignore a0, treat starting capital as a free Real
               variable bounded in [lo, hi]; solver finds cycle AND capital.
    """
    n = market.n
    s = Solver()

    c = [Int(f"c_{t}") for t in range(k)]
    a = [Real(f"a_{t}") for t in range(k + 1)]

    for ci in c:
        s.add(ci >= 0, ci < n)
    s.add(Distinct(*c))

    if a0_bounds is not None:
        lo, hi = a0_bounds
        s.add(a[0] >= lo, a[0] <= hi)
    else:
        s.add(a[0] == a0)

    for t in range(k):
        nxt = c[(t + 1) % k]
        rate_t = rate_lookup(market.rate, n, c[t], nxt)
        fee_t = fee_lookup(fee_vec, n, nxt)
        s.add(a[t + 1] == a[t] * rate_t - fee_t)
        s.add(a[t + 1] >= 0)  # can't go negative -- fee can wipe out the trade

    s.add(a[k] > a[0])  # strictly more than you started with

    if s.check() == sat:
        m = s.model()
        path_ids = [m.evaluate(ci).as_long() for ci in c]
        path_ids.append(path_ids[0])
        a0_val = float(m.evaluate(a[0]).as_fraction())
        ak_val = float(m.evaluate(a[k]).as_fraction())
        return path_ids, a0_val, ak_val
    return None, None, None


def find_arbitrage_cycle_with_fee(market, fee_vec, a0=None, a0_bounds=None, max_k=None):
    n = market.n
    if max_k is None:
        max_k = n
    for k in range(3, max_k + 1):
        cycle, a0_val, ak_val = find_cycle_of_length_with_fee(
            market, fee_vec, k, a0, a0_bounds
        )
        if cycle is not None:
            return cycle, a0_val, ak_val
    return None, None, None
