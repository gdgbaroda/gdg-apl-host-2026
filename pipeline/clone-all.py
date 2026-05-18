#!/usr/bin/env python3
"""Clone all submission repos shallowly into pipeline/<slug>/.
Logs successes / failures to pipeline/_clone-log.json (gitignored)."""
import json, subprocess, pathlib, re, sys, concurrent.futures, time

ROOT = pathlib.Path(__file__).parent
SUBS = json.loads((ROOT / 'submissions.json').read_text())

results = []

def normalize_url(u):
    if not u: return None
    u = u.strip().strip('.').strip(',').rstrip('/')
    # Common patterns: github.com/user/repo, github.com/user/repo.git, github.com/user/repo/tree/...
    m = re.search(r'github\.com[:/]([^/\s]+)/([^/\s#?]+?)(?:\.git)?(?:[/#?]|$)', u)
    if not m: return None
    user, repo = m.group(1), m.group(2)
    repo = re.sub(r'\.git$', '', repo)
    return f'https://github.com/{user}/{repo}.git'

def clone_one(rec):
    slug = rec['_slug']
    raw = rec.get('Source code URL')
    dest = ROOT / slug
    url = normalize_url(raw)
    if not url:
        return {'slug': slug, 'name': rec.get('Full name'), 'raw_url': raw, 'status': 'bad-url'}
    if dest.exists():
        return {'slug': slug, 'name': rec.get('Full name'), 'url': url, 'status': 'exists'}
    try:
        r = subprocess.run(
            ['git', 'clone', '--depth', '1', '--quiet', url, str(dest)],
            capture_output=True, text=True, timeout=90,
        )
        if r.returncode == 0:
            return {'slug': slug, 'name': rec.get('Full name'), 'url': url, 'status': 'ok'}
        else:
            return {'slug': slug, 'name': rec.get('Full name'), 'url': url, 'status': 'fail',
                    'stderr': (r.stderr or '').strip().splitlines()[-1][:200]}
    except subprocess.TimeoutExpired:
        return {'slug': slug, 'name': rec.get('Full name'), 'url': url, 'status': 'timeout'}
    except Exception as e:
        return {'slug': slug, 'name': rec.get('Full name'), 'url': url, 'status': 'exception', 'error': str(e)[:200]}

t0 = time.time()
print(f'cloning {len(SUBS)} repos with 8 parallel workers...', flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(clone_one, r): r for r in SUBS}
    for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
        r = fut.result()
        results.append(r)
        print(f'  [{i:2}/{len(SUBS)}] {r["status"]:8} {r["slug"]}', flush=True)

(ROOT / '_clone-log.json').write_text(json.dumps(results, indent=2))
elapsed = time.time() - t0
print(f'done in {elapsed:.1f}s')
from collections import Counter
print('status counts:', Counter(r['status'] for r in results))
