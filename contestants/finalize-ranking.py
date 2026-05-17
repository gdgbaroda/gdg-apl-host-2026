#!/usr/bin/env python3
"""Recompute ranking.json from:
  - scores-batch-*.json (original vetter scores for HEAD)
  - scores-rollback.json (re-vetter scores for repos rolled back to 23:35 state)
  - rollback-plan.json (state per slug — head-already-in-window, needs-rollback, empty-at-deadline, no-repo)

For each slug:
  - needs-rollback: prefer scores-rollback.json
  - empty-at-deadline: floor scores (1 each, total 5)
  - head-already-in-window: keep original
  - no-repo: keep original

Drops the timing penalty entirely — we're now scoring the in-window state directly.
Outputs ranking.json with contiguous ranks (1..N over public submissions).
"""
import json, pathlib

ROOT = pathlib.Path(__file__).parent
plan = {r['slug']: r for r in json.loads((ROOT / 'rollback-plan.json').read_text())}
subs = {s['_slug']: s for s in json.loads((ROOT / 'submissions.json').read_text())}

# Original vetter scores
original = {}
for i in range(1, 6):
    for s in json.loads((ROOT / f'scores-batch-{i}.json').read_text()):
        original[s['slug']] = s

# Re-vet results
rollback_scores_file = ROOT / 'scores-rollback.json'
rollback = {}
if rollback_scores_file.exists():
    for s in json.loads(rollback_scores_file.read_text()):
        rollback[s['slug']] = s

FLOOR = {'agentic': 1, 'demo': 1, 'quality': 1, 'fit': 1, 'originality': 1}
FLOOR_REASON = (
    "Repository state at the 23:35 event deadline was empty — all commits "
    "arrived afterwards. Scored at the floor since no code was submitted "
    "within the event window."
)

final = []
for slug, orig in original.items():
    state = (plan.get(slug) or {}).get('state', 'unknown')
    rec = dict(orig)  # start from original
    rec['rollback_state'] = state

    if state == 'empty-at-deadline':
        rec['scores'] = dict(FLOOR)
        rec['reason'] = FLOOR_REASON
        rec['ai_evidence'] = 'no in-window code'
    elif state == 'needs-rollback' and slug in rollback:
        rec['scores'] = rollback[slug].get('scores', orig['scores'])
        rec['reason'] = rollback[slug].get('reason', orig['reason'])
        if 'ai_evidence' in rollback[slug]:
            rec['ai_evidence'] = rollback[slug]['ai_evidence']
        if 'demo_check' in rollback[slug]:
            rec['demo_check'] = rollback[slug]['demo_check']
    # else: keep original
    rec['total'] = sum(rec['scores'].get(k, 0) for k in ('agentic','demo','quality','fit','originality'))
    final.append(rec)

# Sort by total desc, tiebreak agentic+fit
def sort_key(s):
    sc = s.get('scores', {})
    return (-s['total'], -(sc.get('agentic', 0) + sc.get('fit', 0)))
final.sort(key=sort_key)
for i, s in enumerate(final, 1):
    s['rank'] = i  # global rank across all 50 (we filter to public in the scoreboard renderer)

(ROOT / 'ranking.json').write_text(json.dumps(final, indent=2))
print(f'wrote ranking.json with {len(final)} records')
print('top 10:')
for s in final[:10]:
    print(f"  #{s['rank']:2}  {s['total']:2}/50  {s['rollback_state']:25s}  {s.get('name','?')[:25]:25s}  {s.get('title','?')[:35]}")
