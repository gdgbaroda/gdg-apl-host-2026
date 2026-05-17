#!/usr/bin/env python3
"""Build web/scoreboard/index.html with:
  - card grid: short bullet summary + 5 score pills + "Details" link
  - modal per project: full reasoning, AI evidence, demo check, links

Single static HTML page, tiny inline JS for modal open/close.
"""
import json, pathlib, html, re

ROOT = pathlib.Path(__file__).parent
WEB = ROOT.parent / 'web' / 'scoreboard'
WEB.mkdir(parents=True, exist_ok=True)

ranking_all = json.loads((ROOT / 'ranking.json').read_text())
# submissions.json is gitignored but local — pull URLs + consent from it.
subs_path = ROOT / 'submissions.json'
sub_by_slug = {}
if subs_path.exists():
    for s in json.loads(subs_path.read_text()):
        sub_by_slug[s['_slug']] = s

# Commit timing analysis (if available)
timing_path = ROOT / 'commit-timing.json'
timing_by_slug = {}
if timing_path.exists():
    for t in json.loads(timing_path.read_text()):
        timing_by_slug[t['slug']] = t

# Penalty schema based on commit-timing verdict
PENALTY = {
    'PRE_EXISTING_ONLY': -5,
    'PRE_EXISTING_THEN_TWEAKED': -5,
    'SINGLE_COMMIT': -2,
}

def penalty_for(slug):
    t = timing_by_slug.get(slug)
    if not t: return 0
    return PENALTY.get(t.get('verdict'), 0)

# Honor the "Can we share your submission publicly?" consent. Anyone who
# answered anything other than "Yes" is filtered out and the visible ranks
# are renumbered 1..N.
def is_public(slug):
    consent = ((sub_by_slug.get(slug, {}) or {}).get('Can we share your submission publicly?') or '').strip().lower()
    return consent == 'yes'

withheld = [s for s in ranking_all if not is_public(s['slug'])]
ranking = [s for s in ranking_all if is_public(s['slug'])]

# Apply commit-timing penalty and recompute totals
for s in ranking:
    p = penalty_for(s['slug'])
    s['original_total'] = s.get('total', 0)
    s['penalty'] = p
    s['total'] = s['original_total'] + p   # p is negative

# Re-sort by adjusted total; tiebreak on agentic + fit then on original total
def sort_key(s):
    sc = s.get('scores', {})
    return (-s['total'], -(sc.get('agentic', 0) + sc.get('fit', 0)), -s['original_total'])
ranking.sort(key=sort_key)
for i, s in enumerate(ranking, 1):
    s['rank'] = i  # contiguous on the public page

def repo_url(slug):
    raw = (sub_by_slug.get(slug, {}) or {}).get('Source code URL', '') or ''
    m = re.search(r'github\.com[:/]([^/\s]+)/([^/\s#?]+?)(?:\.git)?(?:[/#?]|$)', raw.strip())
    if not m: return None
    return f'https://github.com/{m.group(1)}/{m.group(2)}'

def demo_url(slug):
    return (sub_by_slug.get(slug, {}) or {}).get('Live demo/ video URL') or None

def pitch(slug):
    return (sub_by_slug.get(slug, {}) or {}).get('One-line pitch') or None

def what_does_it_do(slug):
    return (sub_by_slug.get(slug, {}) or {}).get('What does it do?') or None

def how_agentic(slug):
    return (sub_by_slug.get(slug, {}) or {}).get('How is it agentic / how did you use AI?') or None

def stack(slug):
    return (sub_by_slug.get(slug, {}) or {}).get('Stack & tools') or None

def short_bullets(entry):
    """Generate 3-4 punchy bullets from the structured scoring data."""
    sc = entry.get('scores', {})
    bullets = []
    # 1. Theme / AI usage
    a = sc.get('agentic', 0)
    ev = entry.get('ai_evidence', '') or ''
    if a >= 8:
        bullets.append(f"💡 Strong AI integration — {ev}" if ev and ev not in ('no AI code found', 'form-only') else "💡 Strong AI/agentic integration")
    elif a >= 5:
        bullets.append(f"💡 Uses AI — {ev}" if ev and ev not in ('no AI code found', 'form-only') else "💡 Uses AI in submission")
    elif a >= 3:
        bullets.append("💡 Light AI usage")
    else:
        bullets.append("💡 No AI / agentic evidence found")

    # 2. Demo
    d = entry.get('demo_check', 'no-url')
    if d == '2xx':
        bullets.append("🟢 Live demo accessible")
    elif d == 'video':
        bullets.append("🎥 Video demo only")
    elif d in ('404', 'timeout', 'fail'):
        bullets.append("⚠️ Demo URL doesn't load")
    else:
        bullets.append("— No live demo submitted")

    # 3. Code quality (or no code)
    q = sc.get('quality', 0)
    has_code = (entry.get('ai_evidence') or '') != 'form-only'
    if not has_code:
        bullets.append("🚫 No public repo to inspect")
    elif q >= 8:
        bullets.append("🛠 Polished, well-structured build")
    elif q >= 5:
        bullets.append("🛠 Functional, mid-tier build")
    else:
        bullets.append("🛠 Sparse / incomplete codebase")

    # 4. Fit + originality combined
    f = sc.get('fit', 0)
    o = sc.get('originality', 0)
    if f >= 8 and o >= 7:
        bullets.append("⭐ Strong challenge fit + original angle")
    elif f >= 8:
        bullets.append("🎯 Directly addresses the challenge")
    elif o >= 8:
        bullets.append("✨ Creative / original approach")
    elif f <= 3:
        bullets.append("❓ Tangential to the brief")
    return bullets

def medal(rank):
    return '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else ''

def fmt_span(minutes):
    if minutes is None: return '—'
    if minutes < 1: return '<1m'
    if minutes < 60: return f'{int(minutes)}m'
    h = minutes / 60
    if h < 24: return f'{h:.1f}h'
    return f'{h/24:.1f}d'

VERDICT_LABEL = {
    'OK': '✅ Active during event',
    'SINGLE_COMMIT': '⚠️ Single commit at submission',
    'NO_COMMITS': '⚠️ Repo has no commits',
    'NO_REPO': '🚫 No public repo',
    'PRE_EXISTING_ONLY': '🚨 No commits during event',
    'PRE_EXISTING_THEN_TWEAKED': '🚨 History pre-dates the event',
    'TEMPLATE_DERIVED': '🧩 Built on a scaffold/template (work in window)',
    'BROAD_TIMELINE': '⚠️ Activity spans multiple days',
    'BULK_DUMP': '⚠️ Bulk push at submission',
}

def commit_summary(slug):
    """Return a short string for the card, e.g. '📅 12 commits · 1.8h' or '— No repo'."""
    t = timing_by_slug.get(slug)
    if not t:
        return None
    v = t.get('verdict', '')
    n = t.get('n_commits') or 0
    span = t.get('span_minutes')
    if v in ('NO_REPO', 'NO_COMMITS'):
        return '📅 No commit history'
    if v == 'SINGLE_COMMIT':
        first = (t.get('first') or '')[:16].replace('T', ' ')
        return f'📅 1 commit at {first}'
    if v == 'PRE_EXISTING_THEN_TWEAKED':
        first = (t.get('first') or '')[:10]
        return f'🚨 {n} commits since {first}'
    if v == 'TEMPLATE_DERIVED':
        return f'🧩 {n - 1} commits on top of a scaffold'
    return f'📅 {n} commits · {fmt_span(span)}'

def render_card(s):
    rank = s['rank']
    total = s['total']
    sc = s.get('scores', {})
    name = html.escape(s.get('name') or '')
    title = html.escape(s.get('title') or '')
    challenge = html.escape(s.get('challenge') or '')
    challenge_class = 'c-blue' if 'Habit' in (s.get('challenge') or '') else 'c-yellow'
    bullets_html = '\n'.join(f'          <li>{html.escape(b)}</li>' for b in short_bullets(s))
    csum = commit_summary(s['slug'])
    commit_html = f'<div class="commits-row">{html.escape(csum)}</div>' if csum else ''
    penalty = s.get('penalty', 0)
    penalty_html = f'<span class="penalty">({penalty})</span>' if penalty else ''
    return f'''
      <article class="card" data-slug="{html.escape(s["slug"])}" tabindex="0" role="button" aria-label="View details for {title}">
        <div class="card-head">
          <div class="rank">{medal(rank)} #{rank}</div>
          <div class="total">{total}<span class="of">/50</span>{penalty_html}</div>
        </div>
        <h2>{title}</h2>
        <div class="meta">
          <span class="name">{name}</span>
          <span class="sep">·</span>
          <span class="challenge {challenge_class}">{challenge}</span>
        </div>
        <ul class="bullets">
{bullets_html}
        </ul>
        {commit_html}
        <div class="scores">
          <span class="score-pill"><span class="score-label">AI</span><span class="score-val">{sc.get("agentic","?")}</span></span>
          <span class="score-pill"><span class="score-label">Demo</span><span class="score-val">{sc.get("demo","?")}</span></span>
          <span class="score-pill"><span class="score-label">Code</span><span class="score-val">{sc.get("quality","?")}</span></span>
          <span class="score-pill"><span class="score-label">Fit</span><span class="score-val">{sc.get("fit","?")}</span></span>
          <span class="score-pill"><span class="score-label">Original</span><span class="score-val">{sc.get("originality","?")}</span></span>
        </div>
        <div class="card-cta">Tap for details →</div>
      </article>'''

def render_modal_data(s):
    """Build the JS-friendly data object for the modal."""
    slug = s['slug']
    t = timing_by_slug.get(slug) or {}
    return {
        'slug': slug,
        'rank': s['rank'],
        'total': s['total'],
        'original_total': s.get('original_total'),
        'penalty': s.get('penalty', 0),
        'medal': medal(s['rank']),
        'name': s.get('name') or '',
        'title': s.get('title') or '',
        'challenge': s.get('challenge') or '',
        'scores': s.get('scores', {}),
        'reason': s.get('reason') or '',
        'ai_evidence': s.get('ai_evidence') or '',
        'demo_check': s.get('demo_check') or '',
        'repo_url': repo_url(slug),
        'demo_url': demo_url(slug),
        'pitch': pitch(slug),
        'what': what_does_it_do(slug),
        'how_agentic': how_agentic(slug),
        'stack': stack(slug),
        'commit_verdict': t.get('verdict'),
        'commit_verdict_label': VERDICT_LABEL.get(t.get('verdict'), '—'),
        'n_commits': t.get('n_commits'),
        'first_commit': t.get('first'),
        'last_commit': t.get('last'),
        'span_minutes': t.get('span_minutes'),
        'span_pretty': fmt_span(t.get('span_minutes')),
        'commits': t.get('commits') or [],
    }

cards_html = '\n'.join(render_card(s) for s in ranking)
modal_data = {s['slug']: render_modal_data(s) for s in ranking}

html_out = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
    <meta name="theme-color" content="#000000" />
    <title>Scoreboard · APL 2026</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@500;700&family=Google+Sans+Text:wght@400;500&display=swap" />
    <link rel="stylesheet" href="/scoreboard/styles.css" />
  </head>
  <body>
    <main class="app">
      <header class="brand">
        <div class="brand-row">
          <span class="dot dot-blue"></span>
          <span class="dot dot-red"></span>
          <span class="dot dot-yellow"></span>
          <span class="dot dot-green"></span>
        </div>
        <h1>Scoreboard</h1>
        <p class="subtitle">APL 2026 · {len(ranking)} of {len(ranking_all)} submissions shown{f" · {len(withheld)} opted out of public listing" if withheld else ""}</p>
        <p class="rubric">Each project scored 1–10 on Agentic AI usage, working demo, code quality, challenge fit, originality — equal weight, max 50. Tap any card for full reasoning.</p>
      </header>
      <section class="cards">{cards_html}
      </section>
      <footer class="foot">GDG Baroda · 2026</footer>
    </main>

    <div id="modal" class="modal hidden" role="dialog" aria-modal="true" aria-labelledby="modal-title" aria-hidden="true">
      <div class="modal-backdrop" data-close="1"></div>
      <div class="modal-card" role="document">
        <button class="modal-close" data-close="1" aria-label="Close">×</button>
        <div id="modal-body"></div>
      </div>
    </div>

    <script id="data" type="application/json">{json.dumps(modal_data)}</script>
    <script src="/scoreboard/app.js"></script>
  </body>
</html>
'''

(WEB / 'index.html').write_text(html_out)
print(f'wrote {WEB / "index.html"} ({len(ranking)} cards)')
