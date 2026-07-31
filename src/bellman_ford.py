"""
Classical baseline: log-transform rates into edge weights, run Bellman-Ford,
a negative-weight cycle corresponds to product-of-rates > 1 (arbitrage).

weight[i][j] = -log(rate[i][j])
sum of weights around a cycle < 0  <=>  product of rates around cycle > 1
"""

import math


def find_negative_cycle(market):
    """
    Returns (cycle, product) where cycle is a list of currency ids
    (cycle[0] == cycle[-1]) and product is the rate product around it,
    or (None, None) if no negative cycle (no arbitrage) exists.
    """
    n = market.n
    weight = [[math.inf] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                weight[i][j] = 0.0
            elif market.rate[i][j] is not None:
                weight[i][j] = -math.log(market.rate[i][j])

    # Standard trick: add a virtual source with 0-weight edges to every node
    # so a negative cycle anywhere is reachable/detectable in one run.
    INF = math.inf
    dist = [0.0] * n          # distance from virtual source (all start at 0)
    pred = [-1] * n

    edges = [(i, j, weight[i][j]) for i in range(n) for j in range(n)
             if i != j and weight[i][j] < INF]

    x = -1
    for it in range(n):
        x = -1
        for (u, v, w) in edges:
            if dist[u] + w < dist[v] - 1e-12:
                dist[v] = dist[u] + w
                pred[v] = u
                x = v

    if x == -1:
        return None, None  # converged before the n-th round -> no negative cycle

    # x is guaranteed to be on (or reachable from) a negative cycle.
    # Walk back n steps to guarantee landing strictly inside the cycle.
    for _ in range(n):
        x = pred[x]

    # Now walk pred pointers from x until we see x again.
    cycle = [x]
    v = pred[x]
    while v != x:
        cycle.append(v)
        v = pred[v]
    cycle.append(x)
    cycle.reverse()

    product = 1.0
    for a, b in zip(cycle, cycle[1:]):
        product *= market.rate[a][b]

    return cycle, product
