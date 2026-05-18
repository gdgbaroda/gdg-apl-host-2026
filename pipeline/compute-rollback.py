#!/usr/bin/env python3
"""For every cloned repo, compute the 'as of 23:35' commit:
  - If there's at least one commit at or before 23:35 IST → that's the rollback SHA
  - Otherwise → the repo is 'empty' at the deadline
Outputs contestants/rollback-plan.json with per-slug info.
"""
import json, subprocess, pathlib
from collections import Counter
from event_config import DATA_DIR, CONFIG

ROOT = pathlib.Path(__file__).parent
log = {r['slug']: r for r in json.loads((ROOT / '_clone-log.json').read_text())}
# event.config.json — naive datetime + timezone field formatted for `git --before`
_tz = CONFIG['event']['window'].get('timezone', 'UTC')
# git --before accepts ISO 8601 directly with offset; use IST default if no offset string supplied
_offset = '+0530' if _tz == 'Asia/Kolkata' else '+0000'
CUTOFF = CONFIG['event']['window']['end'].replace('T', ' ') + ' ' + _offset

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

(DATA_DIR / 'rollback-plan.json').write_text(json.dumps(results, indent=2))
print(Counter(r['state'] for r in results))
print()
for r in results:
    if r['state'] not in ('no-repo', 'head-already-in-window'):
        extra = f" drops={r.get('commits_dropped')}" if r['state'] == 'needs-rollback' else ''
        print(f"  {r['state']:25s}  {r['slug']}{extra}")
