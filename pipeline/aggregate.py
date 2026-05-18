#!/usr/bin/env python3
"""Aggregate all 5 batch score files into a single ranked dataset.
Outputs:
  - <data_dir>/ranking.json — full ranked data
  - <data_dir>/ranking.md   — human-readable ranking
"""
import json, pathlib, sys
from collections import Counter
from event_config import DATA_DIR, EVENT_TITLE, EVENT_YEAR

all_scores = []
missing = []
for i in range(1, 6):
    p = DATA_DIR / f'scores-batch-{i}.json'
    if not p.exists():
        missing.append(p.name)
        continue
    all_scores.extend(json.loads(p.read_text()))

if missing:
    print(f"WARNING: missing {missing}", file=sys.stderr)

# Recompute totals defensively
for s in all_scores:
    sc = s.get('scores', {})
    s['total'] = sum(sc.get(k, 0) for k in ('agentic', 'demo', 'quality', 'fit', 'originality'))

# Sort by total desc, then by agentic + fit (tiebreak on theme adherence)
def sort_key(s):
    sc = s.get('scores', {})
    return (-s['total'], -(sc.get('agentic', 0) + sc.get('fit', 0)))
all_scores.sort(key=sort_key)

# Add rank
for i, s in enumerate(all_scores, 1):
    s['rank'] = i

(DATA_DIR / 'ranking.json').write_text(json.dumps(all_scores, indent=2))

# Markdown report
lines = [f'# {EVENT_TITLE} — Final Ranking ({EVENT_YEAR})', '']
lines.append(f"**{len(all_scores)} submissions scored** across 5 criteria (each 1–10, equal weight).")
lines.append('')
chal_counts = Counter(s.get('challenge') for s in all_scores)
lines.append('**By challenge:** ' + ' · '.join(f"{k}: {v}" for k, v in chal_counts.items()))
lines.append('')
lines.append('| Rank | Total | Name | Project | Challenge | Reason |')
lines.append('|---:|---:|---|---|---|---|')
for s in all_scores:
    reason = (s.get('reason') or '').replace('|', '\\|').replace('\n', ' ')
    lines.append(f"| {s['rank']} | {s['total']}/50 | {s.get('name','?')} | {s.get('title','?')} | {s.get('challenge','?')} | {reason[:240]}{'…' if len(reason)>240 else ''} |")

(DATA_DIR / 'ranking.md').write_text('\n'.join(lines))
print(f"wrote ranking.json + ranking.md ({len(all_scores)} entries)")
print(f"top 5: {[(s['rank'], s.get('name'), s['total']) for s in all_scores[:5]]}")
