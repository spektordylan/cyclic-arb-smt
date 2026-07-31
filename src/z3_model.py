"""
Z3 encoding: does a *simple* cycle of length K exist whose chained
conversion rate exceeds `threshold`?

Variables:
  c_0 .. c_{K-1}: Int in [0, n), the simple cycle (c_K wraps to c_0)
  a_0 .. a_K:     Real, holdings after each hop, a_0 = 1

We require c_0 .. c_{K-1} to be pairwise Distinct so we only search *simple*
cycles. Since a single quoted pair can never itself be profitable (see
rates.py docstring), this also automatically excludes 2-cycles without
needing a special-cased constraint for them -- any simple cycle here has
length >= 3 by construction once K >= 3.

We search K = 3 .. n via iterative deepening rather than fixing one K,
since the profitable cycle length isn't known in advance.
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


def find_cycle_of_length(market, k, threshold=1.0 + 1e-6):
    n = market.n
    s = Solver()

    c = [Int(f"c_{t}") for t in range(k)]
    a = [Real(f"a_{t}") for t in range(k + 1)]

    for ci in c:
        s.add(ci >= 0, ci < n)
    s.add(Distinct(*c))          # simple cycle -> also rules out 2-cycles for k>=3

    s.add(a[0] == 1)
    for t in range(k):
        nxt = c[(t + 1) % k]
        s.add(a[t + 1] == a[t] * rate_lookup(market.rate, n, c[t], nxt))

    s.add(a[k] > threshold)

    if s.check() == sat:
        m = s.model()
        path_ids = [m.evaluate(ci).as_long() for ci in c]
        path_ids.append(path_ids[0])  # close the loop for display
        final = m.evaluate(a[k])
        return path_ids, float(final.as_fraction())
    return None, None


def find_arbitrage_cycle(market, max_k=None, threshold=1.0 + 1e-6):
    """Iterative deepening over cycle length. Returns (cycle, product) for
    the first (shortest) satisfiable K, or (None, None) if none up to max_k."""
    n = market.n
    if max_k is None:
        max_k = n
    for k in range(3, max_k + 1):
        cycle, product = find_cycle_of_length(market, k, threshold)
        if cycle is not None:
            return cycle, product
    return None, None
