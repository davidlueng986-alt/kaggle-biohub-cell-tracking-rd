#!/usr/bin/env bash
# EXP-0045 — H-003 residual: detection gate vs linking opportunity at 4 GT divisions.
# ANALYSIS ONLY. No new detection/linking runs. Deterministic, CPU-only.
# For each GT division (parent + 2 daughters): per-t optimal match (match_nodes,
# 7um, voxel z=1.625/y=x=0.40625) against EXP-0021 IMAGE-graph preds; nearest-
# detected distances; detected-daughter distance; fork/link state at the site.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EXP="$ROOT/experiments/EXP-0045"

python3 - "$ROOT" "$EXP" <<'EOF'
import json, sys
from collections import defaultdict
sys.path.insert(0, sys.argv[1] + '/scripts')
from score import match_nodes, _um_dist, DEFAULT_VOXEL, SCORER_VERSION, PROTOCOL_VERSION
ROOT, EXP = sys.argv[1], sys.argv[2]
vx = DEFAULT_VOXEL

DIVS = {
    '6bba_05db0fb1': [(25000381, 26000400, 26000403),
                      (53001011, 54001033, 54001035),
                      (63001217, 64001240, 64001241)],
    '6bba_062c8d37': [(90001276, 91001298, 91001299)],
}

def nearest_dist(g, cands):
    return min(_um_dist((g['z'], g['y'], g['x']),
                        (n['z'], n['y'], n['x']), vx) for n in cands)

def nearest_node(g, cands):
    return min(cands, key=lambda n: _um_dist((g['z'], g['y'], g['x']),
                                             (n['z'], n['y'], n['x']), vx))

rows = []
for sid, divs in DIVS.items():
    gt = json.load(open(f'{ROOT}/experiments/EXP-0003/gt/{sid}_gt.json'))
    pred = json.load(open(f'{ROOT}/experiments/EXP-0021/{sid}_pred.json'))
    gby = {n['id']: n for n in gt['nodes']}
    pby = {n['id']: n for n in pred['nodes']}
    p2g, g2p = match_nodes(pred['nodes'], gt['nodes'], voxel=vx, max_dist=7.0)
    pe = [tuple(e) for e in pred['edges']]
    pch, ppa = defaultdict(list), defaultdict(list)
    for u, v in pe:
        pch[u].append(v); ppa[v].append(u)
    n_forks = sum(1 for k, v in pch.items() if len(v) >= 2)
    pred_by_t = defaultdict(list)
    for n in pred['nodes']:
        pred_by_t[n['t']].append(n)
    for (p, d1, d2) in divs:
        gp, ga, gb = gby[p], gby[d1], gby[d2]
        mp, ma, mb = g2p.get(p), g2p.get(d1), g2p.get(d2)
        nd = {gid: round(nearest_dist(gby[gid], pred_by_t[gby[gid]['t']]), 3)
              for gid in (p, d1, d2)}
        gt_dd = round(_um_dist((ga['z'], ga['y'], ga['x']),
                               (gb['z'], gb['y'], gb['x']), vx), 3)
        if ma is not None and mb is not None:
            a, b = pby[ma], pby[mb]
            det_dd = round(_um_dist((a['z'], a['y'], a['x']),
                                    (b['z'], b['y'], b['x']), vx), 3)
            det_dids = [ma, mb]
        else:
            n1, n2 = nearest_node(ga, pred_by_t[ga['t']]), nearest_node(gb, pred_by_t[gb['t']])
            det_dd = round(_um_dist((n1['z'], n1['y'], n1['x']),
                                    (n2['z'], n2['y'], n2['x']), vx), 3)
            det_dids = [n1['id'], n2['id']]
        site = {}
        for mid, tag in ((mp, 'parent'), (ma, 'd1'), (mb, 'd2')):
            site[tag] = ({'pred_id': mid, 'in': sorted(ppa.get(mid, [])),
                          'out': sorted(pch.get(mid, []))} if mid is not None else None)
        fork_from_parent = (sorted(pch.get(mp, [])) if mp is not None else [])
        if mp is not None and ma is not None and mb is not None:
            cls = 'RECOVERED' if (set([ma, mb]) <= set(pch.get(mp, []))) else 'LOST-AT-LINKING'
        else:
            cls = 'LOST-AT-DETECTION'
        rows.append({
            'sample': sid, 'gt_parent': p, 'gt_d1': d1, 'gt_d2': d2,
            'gt_t_parent': gp['t'], 'gt_t_daughters': ga['t'],
            'matched_pred': {'parent': mp, 'd1': ma, 'd2': mb},
            'nearest_pred_dist_um': nd,
            'gt_daughter_dist_um': gt_dd,
            'detected_daughter_dist_um': det_dd,
            'detected_daughter_ids': det_dids,
            'fork_edges_from_matched_parent': fork_from_parent,
            'site_edges': site,
            'class': cls,
        })
    # stash per-sample fork count on each row of that sample
    for r in rows:
        if r['sample'] == sid:
            r['pred_forks_in_sample'] = n_forks

n_link = sum(1 for r in rows if r['class'] == 'LOST-AT-LINKING')
verdict = 'GO' if n_link >= 1 else 'STOP'
out = {
    'experiment': 'EXP-0045',
    'protocol_version': PROTOCOL_VERSION,
    'scorer_version': SCORER_VERSION,
    'match': {'max_dist_um': 7.0, 'voxel_size_um': list(vx),
              'method': 'match_nodes per-timepoint optimal assignment'},
    'pred_source': 'experiments/EXP-0021/<sid>_pred.json (IMAGE graphs)',
    'gt_source': 'experiments/EXP-0003/gt/<sid>_gt.json',
    'divisions': rows,
    'summary': {
        'n_divisions': len(rows),
        'n_lost_at_detection': sum(1 for r in rows if r['class'] == 'LOST-AT-DETECTION'),
        'n_lost_at_linking': n_link,
        'n_recovered': sum(1 for r in rows if r['class'] == 'RECOVERED'),
        'verdict': verdict,
    },
}
json.dump(out, open(f'{EXP}/metrics.json', 'w'), indent=2)
print(f'[EXP-0045] {len(rows)} divisions: '
      + ', '.join(f"{r['sample']}:{r['gt_parent']}={r['class']}" for r in rows)
      + f' -> {verdict}')
EOF

echo "[EXP-0045] wrote experiments/EXP-0045/metrics.json"
