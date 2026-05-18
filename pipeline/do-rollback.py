#!/usr/bin/env python3
"""For each repo in rollback-plan.json with state='needs-rollback', detach HEAD
to the rollback SHA so re-vetting sees the as-of-23:35 state."""
import json, subprocess, pathlib
from event_config import DATA_DIR
ROOT = pathlib.Path(__file__).parent
plan = json.loads((DATA_DIR / 'rollback-plan.json').read_text())
for r in plan:
    if r.get('state') != 'needs-rollback': continue
    slug = r['slug']
    sha = r['rollback_sha']
    print(f'rolling back {slug} → {sha}')
    subprocess.run(['git', '-C', slug, 'checkout', '--quiet', sha], check=True)
    short = subprocess.run(['git', '-C', slug, 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    print(f'  HEAD now {short}')
print('done.')
