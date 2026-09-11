# LB ↔ trusted CV calibration

Protocol: v1.2. Public LB is diagnostic only.

## Our submits (trusted vs public)

| Date (HKT) | Kernel / ref | trusted loso_micro | trusted loso_worst | public_lb | gap | Notes |
|------------|--------------|--------------------|--------------------|-----------|-----|-------|
| 2026-09-10 | gold DoG gate-10 v5/v6 `56143782`/`56147475` | 0.4826 (envelope; pre-v1.2 configs, no per-config trusted score) | 0.2092 (envelope) | 0.650 | −0.167 | **FLAG `cv_lb_miscalibrated`** (\|micro−LB\|>0.15): local trusted micro UNDERstates public LB — subset GT sparser/harder per-sample than hidden; T-bonus behaves differently at scale (6 vs ~199 videos). Investigate before ship (§4 gate 4). |
| 2026-09-11 | gold DoG gate-7 v7 `56153940` | 0.4826 (envelope; same caveat) | 0.2092 (envelope) | 0.668 | −0.185 | Same flag. Gate-7 delta (+0.018 LB) consistent in sign with visible probe (+0.002–0.28). |

## External LB (untrusted — never a target)

| Source | public_lb | Why untrusted |
|--------|-----------|---------------|
| Lineage Forge (`56144839`, same account) | 0.946 | Unknown stack / possible public-LB selection; not nested-trusted; do not BTE against this |

