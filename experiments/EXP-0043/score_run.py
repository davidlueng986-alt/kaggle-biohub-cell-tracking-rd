#!/usr/bin/env python3
"""EXP-0043 scorer driver (lives inside EXP dir; scripts/* untouched on disk).

Sample 6bba_062c8d37 is small (~50 det/frame @98.5, ~60 @96): per-frame
N = max(n_pred, n_gt) stays small, so the trusted scorer runs directly with
no solver swap. Both arms use the identical scorer path:
  @96.0  = fresh full-video detect (this rung) + global re-id + BL.link
  @98.5  = FROZEN EXP-0021 pred, rescored fresh (recompute-by-rescoring)
Recall diagnostic uses score.match_nodes, same definition as EXP-0021.
"""
import json
import os
import sys
import time

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from score import score_samples, match_nodes  # noqa: E402 trusted scorer v1.1.0

SID = "6bba_062c8d37"


def main():
    t0 = time.time()
    gt = json.load(open(os.path.join(ROOT, "experiments/EXP-0003/gt",
                                     f"{SID}_gt.json")))
    assert gt.get("T_true") == 6030, gt.get("T_true")

    # ---- @96.0 diagnostics (recall/det/timing) + trusted score
    det_total, times, recs = 0, [], []
    for t in range(100):
        det = json.load(open(os.path.join(EXP_DIR, f"full_{SID}_t{t}.json")))
        times.append(det["params"]["elapsed_s"])
        det_total += len(det["nodes"])
        g = [n for n in gt["nodes"] if int(n["t"]) == t]
        if g:
            _, g2p = match_nodes(det["nodes"], g)
            recs.append(len(g2p) / len(g))
    recall96 = sum(recs) / len(recs)
    s_f = sum(times) / len(times)
    print(f"@96.0: det_total={det_total} det/f={det_total/100:.2f} "
          f"recall={recall96:.4f} s_f={s_f:.4f}", flush=True)

    pred96 = json.load(open(os.path.join(EXP_DIR, f"{SID}_pred.json")))
    ts = time.time()
    agg96 = score_samples([(SID, pred96, gt, None)])
    print(f"score96 took {time.time()-ts:.1f}s", flush=True)
    s96 = agg96["per_sample"][0]
    print(json.dumps(s96, indent=2), flush=True)

    # ---- @98.5 baseline RECOMPUTE: fresh scorer run on frozen EXP-0021 pred
    pred98 = json.load(open(os.path.join(
        ROOT, "experiments/EXP-0021", f"{SID}_pred.json")))
    ts = time.time()
    agg98 = score_samples([(SID, pred98, gt, None)])
    print(f"score98 took {time.time()-ts:.1f}s", flush=True)
    s98 = agg98["per_sample"][0]
    print(json.dumps(s98, indent=2), flush=True)

    out = {
        "p96": {"recall": recall96, "det_f": det_total / 100,
                "gid": det_total, "s_f": s_f,
                "T_ratio": det_total / s98["T_true"],
                "edge": s96["adjusted_edge_jaccard"],
                "raw": s96["edge_jaccard_raw"],
                "div": s96["division_jaccard"],
                "score": s96["score"], "ec": s96["edge_counts"],
                "dc": s96["division_counts"], "T_true": s96["T_true"],
                "T_pred": s96["T_pred"],
                "assign": pred96.get("assign")},
        "p98": {"edge": s98["adjusted_edge_jaccard"],
                "raw": s98["edge_jaccard_raw"],
                "div": s98["division_jaccard"], "score": s98["score"],
                "ec": s98["edge_counts"], "dc": s98["division_counts"],
                "T_true": s98["T_true"], "T_pred": s98["T_pred"],
                "T_ratio": s98["T_pred"] / s98["T_true"]},
        "scorer": {"protocol": agg96["protocol_version"],
                   "scorer_version": agg96["scorer_version"],
                   "solver": "trusted pure-python Hungarian unmodified "
                             "(small-N sample, no swap needed)",
                   "scripts_unmodified": True},
        "wall_s": time.time() - t0,
    }
    json.dump(out, open(os.path.join(EXP_DIR, "scores.json"), "w"), indent=2)
    print(f"WROTE scores.json wall={out['wall_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
