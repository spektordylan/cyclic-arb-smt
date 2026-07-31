"""
Bid/ask-aware rate matrix construction.

Convention
----------
For each unordered currency pair {i, j} there is ONE venue quoting a single
mid price `mid_ij` = amount of currency i needed to buy 1 unit of currency j,
plus a half-spread `h` (same for all pairs here, but doesn't have to be).

  ask_ij = mid_ij * (1 + h)   # i you must pay to BUY 1 unit of j
  bid_ij = mid_ij * (1 - h)   # i you RECEIVE for selling 1 unit of j

Directional conversion rates (amount of target currency received per 1 unit
of source currency):

  rate[i][j] = 1 / ask_ij       # converting i -> j: you're buying j with i
  rate[j][i] = bid_ij           # converting j -> i: you're selling j for i

This guarantees, for every single pair and independent of mid_ij:

  rate[i][j] * rate[j][i] = (1 - h) / (1 + h) < 1

i.e. round-tripping on a single quoted pair always loses money. Any
profitable cycle therefore *requires* length >= 3 and reflects a genuine
cross-pair inconsistency, not just "the spread let you profit."
"""

from dataclasses import dataclass


@dataclass
class Market:
    names: list          # currency names, index = currency id
    rate: list            # rate[i][j] = units of j received per 1 unit of i
    n: int


def build_market(names, pair_mids, half_spread):
    """
    names: list[str], length n
    pair_mids: dict[(i, j)] -> mid_ij for i < j (amount of currency i per 1
               unit of currency j)
    half_spread: float, e.g. 0.0005 for 5 bps
    """
    n = len(names)
    rate = [[None] * n for _ in range(n)]

    for i in range(n):
        rate[i][i] = 1.0

    for (i, j), mid in pair_mids.items():
        assert i < j, f"pair_mids keys must be (i, j) with i < j, got ({i}, {j})"
        ask_ij = mid * (1 + half_spread)   # i-cost to buy 1 j
        bid_ij = mid * (1 - half_spread)   # i-received selling 1 j

        rate[i][j] = 1.0 / ask_ij   # i -> j
        rate[j][i] = bid_ij         # j -> i

    for i in range(n):
        for j in range(n):
            if rate[i][j] is None:
                raise ValueError(f"missing quote for pair ({i}, {j})")

    return Market(names=names, rate=rate, n=n)


def planted_example():
    """
    4 currencies. Pairs involving C3 are set consistently with C0/C1/C2 mids
    (mid_i3 ~= mid_ij * mid_j3), so C3 contributes no extra arbitrage and is
    there purely to check the detector doesn't hallucinate a cycle through it.

    The C0/C1/C2 triangle is deliberately mispriced: mid_02 is quoted lower
    than what mid_01 * mid_12 would imply, which opens a real arbitrage on
    the cycle C0 -> C2 -> C1 -> C0 even after eating the spread on all three
    legs.
    """
    names = ["C0", "C1", "C2", "C3"]
    pair_mids = {
        (0, 1): 1.10,
        (1, 2): 0.95,
        (0, 2): 1.00,   # "should" be ~1.045 if consistent with 0-1-2 -> mispriced
        (0, 3): 1.50,   # consistent: 1.10 * 1.36
        (1, 3): 1.36,
        (2, 3): 1.43,   # consistent: (1/0.95) * 1.36 ~= 1.4316
    }
    half_spread = 0.0005  # 5 bps
    return build_market(names, pair_mids, half_spread)


def cycle_product(market, cycle):
    """cycle: list of currency ids, cycle[0] == cycle[-1]. Returns product of
    directional rates along the cycle (>1 means profitable)."""
    p = 1.0
    for a, b in zip(cycle, cycle[1:]):
        p *= market.rate[a][b]
    return p
