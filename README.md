# cyclic-arb-smt

This project implements an SMT-based cross-curency arbitrage detector for a list of hypothetical currencies. 

### Baseline Comparison

We first implement the SMT solution on the simplest case: a list of currencies on the same exchange, with no fees. The typical procedure for detecting arbitrage in this case is the [Bellman-Ford algorithm](https://en.wikipedia.org/wiki/Bellman%E2%80%93Ford_algorithm), which efficiently detects __ through a simple ___. We compare the Bellman-Ford result to our Z3 SMT-based model, confirming that they detect the same opportunity: 

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

With this baseline check completed, we move onto more complex cases in which Bellman-Ford may become intractable, demonstrating the versatility of the SMT-based implementation. 