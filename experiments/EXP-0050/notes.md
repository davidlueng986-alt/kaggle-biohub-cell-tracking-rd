# Notes — EXP-0050

## Outcome: MIXED (gate7 wins 4/6; gate10 flips 2/6)

Per-sample adj (gate7 vs gate10) + edge TP/FP/FN moves (g7 -> g10):
- 44b6_0113de3b: 0.938214 vs 0.660561 (d=+0.2777) 47/2/3 -> 42/16/8. Gate10 floods FPs.
- 6bba_05b6850b: 0.819438 vs 0.813416 (d=+0.0060) 699/30/146 -> 701/39/144.
- 44b6_0b24845f: 0.103959 vs 0.101960 (d=+0.0020) 5/2/44 -> 5/3/44.
- 44b6_0c582fdc: 0.095845 vs 0.121649 (d=-0.0258, FLIP) 7/7/63 -> 9/8/61.
- 6bba_05db0fb1: 0.209169 vs 0.192097 (d=+0.0171) 251/92/932 -> 241/150/942.
- 6bba_062c8d37: 0.864702 vs 0.877787 (d=-0.0131, FLIP) 781/20/117 -> 798/26/100.

## Reproduction check
Gate7 adj bit-matches frozen references: 0113de3b 0.938214 (EXP-0021),
05b6850b 0.819438 (EXP-0009), 0b24845f 0.103959 + 0c582fdc 0.095845 (EXP-0021).

## Mechanism hypotheses for flips
Both flips share one mechanism: gate-10 recovers genuine 7-10um frame
displacements; verdict per sample = TP gain vs FP cost.
- 44b6_0c582fdc (sparse, recall~0.20, denom TP+FP+FN=77): +2 TP/-2 FN at +1 FP
  moves raw 0.0909->0.1154. Small denominators amplify each recovered edge.
- 6bba_062c8d37 (dense, high-recall): +17 TP/-17 FN (fast cells) at +6 FP, net win.
- Contrast 6bba_05db0fb1 (dense, low recall): gate10 adds +58 FP for -10 TP net
  (TP 251->241) -> loses. FP cost dominates where density high but motion slow.
So the gate tradeoff is density x motion dependent, not uniform; matches the
oracle arm preferring gate-10 while IMAGE graphs mostly prefer gate-7.

## Division counts (unchanged by gate, as expected)
Linker emits <=1 outgoing edge/node -> zero forks: dc=0/0/0 (div jaccard 1.0 by
empty-convention) on 4 div-free samples; dc=0/0/3 (05db0fb1) and 0/0/1 (062c8d37)
where GT has divisions the linker cannot predict.

## Next-stage input
Verdict MIXED. Submit-gate-7 decision does NOT stand on 6/6 evidence (stands 4/6).
Recommend per-sample/per-regime gate, or gate-10 only where motion warrants it;
do not globally flip to gate-10 (0113de3b collapses -0.28 under gate-10).
