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

### Additional Conditions

Two further conditions were added to the Z3 model, each breaking Bellman-Ford's fixed-edge-weight assumption in a different way. Nonlinear slippage models the realized rate as degrading with trade size, `effective_rate = base_rate * (1 - impact * a_t)`, making the per-hop transition quadratic rather than affine; unlike a fixed fee, slippage favors smaller trades, since price impact is negligible at small size. Integer lot sizes require holdings to round down to the nearest lot via an existential integer variable, `m_t * lot <= raw_output < (m_t + 1) * lot`; the resulting rounding loss depends on the solved-for value of `a_t`, which has no shortest-path analog.

We combine bid/ask spreads, fixed fees, slippage, and lot sizes into a single model (`z3_full_model.py`) and compare its results against Bellman-Ford across a range of starting capital. Bellman-Ford's verdict remains fixed at 4.738% throughout, since it is blind to the three added conditions. The combined Z3 model instead reveals a bounded interior region of profitability: unprofitable below approximately `a0 = 0.35`, where fees and lot rounding dominate; profitable within a middle range peaking near `a0 = 1.2` to `1.6`; and unprofitable again above approximately `a0 = 5.3`, where slippage dominates (`fig4_adaptability_comparison.png`). This capital-dependent "sweet spot" has no equivalent in the Bellman-Ford formulation, which has no mechanism for representing conditions that depend on trade size at all.

The remaining figures summarize this comparison more broadly. `fig1_profit_vs_capital.png` plots profitability against starting capital across the fee-only, slippage-only, and combined scenarios, against Bellman-Ford's flat baseline. `fig2_solve_time_scaling.png` compares solve time as market size grows on the frictionless case, where Bellman-Ford remains roughly 500x faster. `fig3_capability_matrix.png` summarizes which conditions each method can represent. Taken together, the results indicate that Bellman-Ford is preferable when it is applicable and speed is a priority, but becomes unusable as soon as trade-size-dependent conditions are introduced, while the Z3 formulation extends to these cases without a change in structure and is clearly a powerful approach due to its versatility.