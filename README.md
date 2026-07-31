# cyclic-arb-smt

This project implements an SMT-based cross-curency arbitrage detector for a list of hypothetical currencies. 

### Baseline Comparison

We first implement the SMT solution on the simplest case: a list of currencies on the same exchange, with no fees. The typical procedure for detecting cross-currency arbitrage is the [Bellman-Ford algorithm](https://en.wikipedia.org/wiki/Bellman%E2%80%93Ford_algorithm), which detects profitable cycles by representing exchange rates as graph edge weights using the negative logarithm transformation. We compare the Bellman-Ford result to our Z3 SMT-based model with `validate.py`, confirming that they detect the same opportunity:

```
=== Bellman-Ford ===
cycle:   C3 -> C0 -> C2 -> C3
product: 1.047379  (profit: 4.738%)

=== Z3 (iterative deepening K=3..n) ===
cycle:   C2 -> C3 -> C0 -> C2
product: 1.047379  (profit: 4.738%)

=== Agreement check ===
Bellman-Ford product recomputed independently: 1.047379
Z3 product recomputed independently:            1.047379
Same currencies involved: True
Both profitable:          True
```

With this baseline check completed, we move onto more complex cases in which Bellman-Ford may become intractable, demonstrating the versatility of the SMT-based implementation.

### Fixed Fees

Bellman-Ford's edge weights are fixed numbers, so its verdict on whether a cycle is profitable is the same at every trade size. A fixed per-trade fee (e.g. $2 flat, rather than a percentage) breaks this assumption: the fee is negligible on a large trade and dominant on a small one, so profitability becomes a function of starting capital rather than a scale-invariant property of the rates alone. Bellman-Ford has no starting-capital parameter and cannot represent this condition at all.

We extend the Z3 model (`z3_fee_model.py`) with a flat fee subtracted per hop, and with starting capital `a0` as either a fixed value or a free variable bounded within a search range. `compare_with_fees.py` produces:

```
+--------------------+-------------------------------+------------------------------------------------+
| Capital regime     | Bellman-Ford (fee-blind)      | Fee-aware Z3                                   |
+====================+===============================+================================================+
| a0 = 0.30          | 4.738% (C3 -> C0 -> C2 -> C3) | UNSAT                                          |
+--------------------+-------------------------------+------------------------------------------------+
| a0 = 2.00          | 4.738% (C3 -> C0 -> C2 -> C3) | SAT: 2.772% (C0 -> C2 -> C1 -> C0)             |
+--------------------+-------------------------------+------------------------------------------------+
| a0 ∈ [0.01, 0.45]  | 4.738% (C3 -> C0 -> C2 -> C3) | UNSAT                                          |
+--------------------+-------------------------------+------------------------------------------------+
| a0 ∈ [0.01, 10.00] | 4.738% (C3 -> C0 -> C2 -> C3) | SAT: a0 = 10.00, 4.034% (C2 -> C1 -> C0 -> C2) |
+--------------------+-------------------------------+------------------------------------------------+
```

Bellman-Ford's flat verdict is wrong at `a0 = 0.30`, coincidentally right at `a0 = 2.00`, and cannot be asked the `a0`-range questions at all due to being ill-posed. Brute-force enumeration over every simple cycle and starting currency in this market puts the true minimum breakeven capital at 0.5060; below it, no cycle is profitable at any fee-adjusted trade size. Thus, applying the typical Bellman-Ford for cross-currency arbitrage detection is not feasible in this case, whereas the Z3 solution is versatile and expressive, correctly responding to different fee scenarios. 