#!/usr/bin/env python3
"""For every cloned repo, compute the 'as of 23:35' commit:
  - If there's at least one commit at or before 23:35 IST → that's the rollback SHA
  - Otherwise → the repo is 'empty' at the deadline
Outputs contestants/rollback-plan.json with per-slug info.
"""
import json, subprocess, pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).parent
log = {r['slug']: r for r in json.loads((ROOT / '_clone-log.json').read_text())}
CUTOFF = '2026-05-16 23:49:00 +0530'  # IST

def cmd(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=20).stdout.strip()

results = []
for slug, r in log.items():
    if r.get('status') != 'ok':
        results.append({'slug': slug, 'state': 'no-repo'})
        continue
    repo = str(ROOT / slug)
    cur_head = cmd(['git', '-C', repo, 'rev-parse', 'HEAD'])
    rollback = cmd(['git', '-C', repo, 'rev-list', '-1', f'--before={CUTOFF}', 'HEAD'])
    if not rollback:
        results.append({
            'slug': slug, 'state': 'empty-at-deadline',
            'current_head': cur_head[:12], 'rollback_sha': None,
        })
    elif rollback == cur_head:
        results.append({
            'slug': slug, 'state': 'head-already-in-window',
            'current_head': cur_head[:12], 'rollback_sha': rollback[:12],
        })
    else:
        # Count commits dropped by rollback
        dropped = cmd(['git', '-C', repo, 'rev-list', '--count', f'{rollback}..HEAD'])
        results.append({
            'slug': slug, 'state': 'needs-rollback',
            'current_head': cur_head[:12], 'rollback_sha': rollback[:12],
            'commits_dropped': int(dropped) if dropped.isdigit() else None,
        })

(ROOT / 'rollback-plan.json').write_text(json.dumps(results, indent=2))
print(Counter(r['state'] for r in results))
print()
for r in results:
    if r['state'] not in ('no-repo', 'head-already-in-window'):
        extra = f" drops={r.get('commits_dropped')}" if r['state'] == 'needs-rollback' else ''
        print(f"  {r['state']:25s}  {r['slug']}{extra}")
