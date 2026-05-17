#!/usr/bin/env python3
"""Analyze commit timing for every cloned repo.
Computes first-commit, last-commit, # commits during the event window.

Event window is estimated from submission timestamps in submissions.json:
the earliest submission marks roughly the end of the event (submissions
opened at the close). Backwards-extend by ~6 hours for the hackathon
session itself.

Flags:
  - PRE_EXISTING: first commit > 24h before event start
  - BULK_DUMP:    >50% of commits within a 5-min window AND that window
                  is the only activity (typical "git init && commit -am
                  'done'" pattern)
  - OK:           commits span the event window normally
"""
import json, pathlib, subprocess, datetime as dt
from collections import Counter

ROOT = pathlib.Path(__file__).parent
subs = json.loads((ROOT / 'submissions.json').read_text())
log = {r['slug']: r for r in json.loads((ROOT / '_clone-log.json').read_text())}

# Estimate event window from submission timestamps
ts_strings = [s.get('Timestamp') for s in subs if s.get('Timestamp')]
ts_dts = []
for s in ts_strings:
    try:
        ts_dts.append(dt.datetime.fromisoformat(s.replace('Z', '+00:00').split('+')[0]))
    except Exception:
        pass
ts_dts.sort()
event_end = ts_dts[-1] if ts_dts else None
event_start_est = ts_dts[0] - dt.timedelta(hours=2) if ts_dts else None
# Hackathon was 1 day; assume start window from ~6h before first submission
event_window_start = (ts_dts[0] - dt.timedelta(hours=12)) if ts_dts else None
print(f"submissions submitted between: {ts_dts[0]} → {ts_dts[-1]}")
print(f"assumed event window: {event_window_start} → {event_end}")
print()

def git_log_iso(slug):
    """Return list of (datetime, subject) for every commit on every ref."""
    repo = ROOT / slug
    if not repo.exists(): return None
    try:
        out = subprocess.run(
            ['git', '-C', str(repo), 'log', '--all', '--pretty=format:%aI%x09%s'],
            capture_output=True, text=True, timeout=20,
        )
        if out.returncode != 0: return None
        commits = []
        for ln in out.stdout.strip().splitlines():
            if '\t' not in ln: continue
            ts, msg = ln.split('\t', 1)
            try:
                commits.append((dt.datetime.fromisoformat(ts).replace(tzinfo=None), msg.strip()))
            except Exception:
                pass
        return commits
    except Exception:
        return None

def analyze(slug, commits_with_msg, window_start, window_end):
    if not commits_with_msg:
        return {'slug': slug, 'verdict': 'NO_COMMITS', 'first': None, 'last': None,
                'n_commits': 0, 'n_in_window': 0, 'span_minutes': 0, 'commits': []}
    commits_sorted = sorted(commits_with_msg, key=lambda x: x[0])
    times = [c[0] for c in commits_sorted]
    first, last = times[0], times[-1]
    in_win = [c for c in times if window_start - dt.timedelta(hours=12) <= c <= window_end + dt.timedelta(hours=12)]
    span = (last - first).total_seconds() / 60.0
    n = len(times)

    pre_existing = first < (window_start - dt.timedelta(hours=24))

    # Template-derived: ONE old commit (acting as the scaffold seed),
    # then everything else happens inside the event window.
    template_seed = False
    if pre_existing and n >= 2:
        old = [c for c in times if c < (window_start - dt.timedelta(hours=24))]
        new_in_win = [c for c in times if c >= (window_start - dt.timedelta(hours=24))]
        if len(old) == 1 and len(new_in_win) >= 1:
            template_seed = True
            # Strengthen the signal if message obviously looks like a template
            seed_msg = commits_sorted[0][1].lower()
            if any(k in seed_msg for k in ['template:', 'scaffold', 'starter', 'boilerplate', 'init']):
                template_seed = True  # explicit confirmation, already True

    bulk = False
    if n >= 3 and span < 5:
        bulk = True
    elif n >= 5:
        biggest_cluster = 0
        for i in range(n):
            j = i
            while j + 1 < n and (times[j+1] - times[i]).total_seconds() <= 5 * 60:
                j += 1
            biggest_cluster = max(biggest_cluster, j - i + 1)
        if biggest_cluster / n > 0.7:
            bulk = True

    if template_seed:
        verdict = 'TEMPLATE_DERIVED'
    elif pre_existing and last < window_start:
        verdict = 'PRE_EXISTING_ONLY'
    elif pre_existing:
        verdict = 'PRE_EXISTING_THEN_TWEAKED'
    elif n == 1:
        verdict = 'SINGLE_COMMIT'
    elif bulk:
        verdict = 'BULK_DUMP'
    elif span > 60 * 12:
        verdict = 'BROAD_TIMELINE'
    else:
        verdict = 'OK'

    return {
        'slug': slug, 'verdict': verdict,
        'first': first.isoformat(timespec='minutes'),
        'last': last.isoformat(timespec='minutes'),
        'first_msg': commits_sorted[0][1][:120],
        'n_commits': n, 'span_minutes': round(span, 1),
        'n_in_window': len(in_win),
        'commits': [c.isoformat(timespec='minutes') for c in times],
    }

results = []
for slug, r in log.items():
    if r['status'] != 'ok':
        results.append({'slug': slug, 'verdict': 'NO_REPO'})
        continue
    commits = git_log_iso(slug)
    results.append(analyze(slug, commits, event_window_start, event_end))

(ROOT / 'commit-timing.json').write_text(json.dumps(results, indent=2))

print(f"{'Verdict':30s}  count")
print('-' * 40)
for verdict, count in Counter(r['verdict'] for r in results).most_common():
    print(f"{verdict:30s}  {count}")

print()
print("=== PRE_EXISTING_ONLY (probably pre-built) ===")
for r in results:
    if r['verdict'] == 'PRE_EXISTING_ONLY':
        print(f"  {r['slug']:55s}  first={r['first']}  last={r['last']}  n={r['n_commits']}")

print()
print("=== PRE_EXISTING_THEN_TWEAKED ===")
for r in results:
    if r['verdict'] == 'PRE_EXISTING_THEN_TWEAKED':
        print(f"  {r['slug']:55s}  first={r['first']}  last={r['last']}  n={r['n_commits']}")

print()
print("=== BULK_DUMP (single-push pattern) ===")
for r in results:
    if r['verdict'] == 'BULK_DUMP':
        print(f"  {r['slug']:55s}  first={r['first']}  last={r['last']}  n={r['n_commits']}  span={r['span_minutes']}min")
