#!/usr/bin/env python3
"""Restore rolled-back repos to their original HEAD (stored in rollback-plan.json)."""
import json, subprocess, pathlib
ROOT = pathlib.Path(__file__).parent
plan = json.loads((ROOT / 'rollback-plan.json').read_text())
for r in plan:
    if r.get('state') != 'needs-rollback': continue
    slug = r['slug']
    sha = r['current_head']
    res = subprocess.run(['git', '-C', slug, 'checkout', '--quiet', sha], capture_output=True, text=True)
    if res.returncode == 0:
        print(f'  restored {slug} → {sha}')
    else:
        print(f'  ✗ {slug}: {(res.stderr or "").strip()[:120]}')
