"""EXP-0052: parse v7 visible log + local det calibration + hidden projections.

Reads the fetched v7 kernel log (JSON array of {stream_name,time,data}),
extracts the per-video timing table, fits local detection s/frame vs
det/frame from frozen EXP-0008/0009/0021 per-frame artifacts, anchors an
absolute model on the 4 Kaggle per-video totals, and projects hidden cost
for 199 videos x 100 frames under sparse/mix/dense regimes.

CPU-only, deterministic, stdlib only.
"""
import argparse
import glob
import json
import re
import statistics as st


def linfit(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    b = sxy / sxx if sxx else 0.0
    a = my - b * mx
    r2 = (sxy ** 2 / (sxx * syy)) if (sxx and syy) else 0.0
    return a, b, r2


def parse_v7_log(path):
    recs = json.load(open(path))  # whole file is one JSON array
    pat = re.compile(r"\[(\d+)/(\d+)\]\s+(\S+):\s+pct=(\S+)\s+T=(\d+)\s+"
                     r"det=(\d+)\s+edges=(\d+)\s+(\S+)s\s+\(elapsed\s+(\S+)h")
    videos = []
    wrote_total_h = None
    for r in recs:
        d = r.get("data", "")
        if not isinstance(d, str):
            continue
        m = pat.search(d)
        if m:
            videos.append({
                "k": int(m.group(1)), "n": int(m.group(2)),
                "sample": m.group(3), "pct": float(m.group(4)),
                "T": int(m.group(5)), "det": int(m.group(6)),
                "edges": int(m.group(7)), "seconds": float(m.group(8)),
                "elapsed_h": float(m.group(9)),
            })
        m2 = re.search(r"WROTE \S+: \d+ rows, \d+ datasets, total (\S+)h", d)
        if m2:
            wrote_total_h = float(m2.group(1))
    videos.sort(key=lambda v: v["k"])
    return videos, wrote_total_h, len(recs)


def load_local_frames(root):
    recs = []
    for e in ["EXP-0008", "EXP-0009", "EXP-0021"]:
        for f in glob.glob(f"{root}/experiments/{e}/full_*.json"):
            if not re.search(r"_t\d+\.json$", f):
                continue
            d = json.load(open(f))
            sample = re.match(r".*full_(.*)_t\d+", f).group(1)
            recs.append({"exp": e, "sample": sample,
                         "n_components": d["params"]["n_components"],
                         "n_kept": len(d["nodes"]),
                         "elapsed_s": d["params"]["elapsed_s"],
                         "pct": d["params"].get("pct")})
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--hidden-videos", type=int, default=199)
    ap.add_argument("--frames-per-video", type=int, default=100)
    ap.add_argument("--cap-h", type=float, default=12.0)
    args = ap.parse_args()

    videos, wrote_total_h, n_log_recs = parse_v7_log(args.log)
    assert len(videos) == 4, f"expected 4 per-video lines, got {len(videos)}"
    total_s = sum(v["seconds"] for v in videos)
    total_h = total_s / 3600.0

    frames = load_local_frames(args.root)
    xs_nc = [r["n_components"] for r in frames]
    xs_k = [r["n_kept"] for r in frames]
    ys = [r["elapsed_s"] for r in frames]
    a_nc, b_nc, r2_nc = linfit(xs_nc, ys)
    a_k, b_k, r2_k = linfit(xs_k, ys)

    # Kaggle-anchored absolute model: per-video total s/frame vs det/frame.
    kg_x = [v["det"] / v["T"] for v in videos]
    kg_y = [v["seconds"] / v["T"] for v in videos]
    a_kg, b_kg, r2_kg = linfit(kg_x, kg_y)

    # det/frame regimes from local kept counts pooled by sample.
    by_sample = {}
    for r in frames:
        by_sample.setdefault(r["sample"], []).append(r["n_kept"])
    regime_mean = {s: st.mean(v) for s, v in by_sample.items()}
    sparse = min(regime_mean.values())          # 6bba_05b6850b-like
    dense = max(regime_mean.values())           # 6bba_05db0fb1-like
    mix = sum(v["det"] / v["T"] for v in videos) / len(videos)  # visible mix
    sparse_src = min(regime_mean, key=regime_mean.get)
    dense_src = max(regime_mean, key=regime_mean.get)

    n_frames = args.hidden_videos * args.frames_per_video
    projections = {}
    for name, d in [("sparse_best", sparse), ("observed_mix", mix),
                    ("dense_worst", dense), ("double_dense_robustness", 2 * dense)]:
        s_per_frame = a_kg + b_kg * d
        tot_s = s_per_frame * n_frames
        tot_h = tot_s / 3600.0
        projections[name] = {
            "det_per_frame": round(d, 2),
            "s_per_frame": round(s_per_frame, 4),
            "total_s": round(tot_s, 1),
            "total_h": round(tot_h, 3),
            "headroom_vs_cap": round(args.cap_h / tot_h, 3),
        }

    verdict = ("fits" if all(p["total_h"] < args.cap_h
                              for p in projections.values()) else "EXCEEDS")
    metrics = {
        "v7_log_records": n_log_recs,
        "visible_per_video": videos,
        "visible_total_s": total_s,
        "visible_total_h": round(total_h, 4),
        "visible_wrote_total_h": wrote_total_h,
        "visible_matches_0_12h": abs(total_h - 0.12) < 0.005,
        "hidden_rerun_in_log": False,
        "local_frames_n": len(frames),
        "local_fit_vs_n_components": {"intercept_s": round(a_nc, 4),
                                      "slope_s_per_det": round(b_nc, 6),
                                      "r2": round(r2_nc, 4)},
        "local_fit_vs_n_kept": {"intercept_s": round(a_k, 4),
                                "slope_s_per_det": round(b_k, 6),
                                "r2": round(r2_k, 4)},
        "kaggle_fit_s_per_frame": {"intercept_s": round(a_kg, 4),
                                   "slope_s_per_det": round(b_kg, 6),
                                   "r2": round(r2_kg, 4), "n": 4},
        "regime_det_per_frame": {s: round(v, 2)
                                 for s, v in sorted(regime_mean.items())},
        "regime_sources": {"sparse_best": sparse_src, "dense_worst": dense_src},
        "projection_basis": {"hidden_videos": args.hidden_videos,
                             "frames_per_video": args.frames_per_video,
                             "total_frames": n_frames, "cap_h": args.cap_h},
        "projections_h": projections,
        "verdict": verdict,
    }
    with open(args.out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps({"visible_total_h": round(total_h, 4),
                      "local_R2_kept": round(r2_k, 4),
                      "kaggle_R2": round(r2_kg, 4),
                      "projections_h": {k: v["total_h"]
                                        for k, v in projections.items()},
                      "verdict": verdict}, indent=2))


if __name__ == "__main__":
    main()
