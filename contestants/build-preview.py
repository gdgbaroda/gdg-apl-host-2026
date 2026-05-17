#!/usr/bin/env python3
"""Build web/preview/index.html — interactive homepage celebrating the APL event."""
import json, pathlib, html, re, datetime as dt
from collections import Counter

ROOT = pathlib.Path(__file__).parent
OUT = ROOT.parent / 'web' / 'preview'
OUT.mkdir(parents=True, exist_ok=True)

subs = json.loads((ROOT / 'submissions.json').read_text())
ranking = json.loads((ROOT / 'ranking.json').read_text())
timing = json.loads((ROOT / 'commit-timing.json').read_text())
sub_by_slug = {s['_slug']: s for s in subs}
timing_by_slug = {t['slug']: t for t in timing}

def is_public(slug):
    return ((sub_by_slug.get(slug, {}) or {}).get('Can we share your submission publicly?') or '').strip().lower() == 'yes'

public_ranking = [s for s in ranking if is_public(s['slug'])]
# Re-rank contiguously for display
public_ranking.sort(key=lambda x: (-x['total'], -(x['scores'].get('agentic', 0) + x['scores'].get('fit', 0))))
for i, s in enumerate(public_ranking, 1):
    s['rank'] = i

# ---- Stats ----
total_subs = len(ranking)
public_count = len(public_ranking)
challenge_counts = Counter(s.get('Which challenge?') or '?' for s in subs)
empty_count = sum(1 for t in timing if t.get('verdict') in ('NO_COMMITS', 'POST_EVENT_ONLY'))

# Count total commits inside the event window (18:00 – 23:49)
WIN_START = dt.datetime(2026, 5, 16, 18, 0)
WIN_END = dt.datetime(2026, 5, 16, 23, 49)
in_window_commits = []  # list of (datetime, slug, score)
score_by_slug = {s['slug']: s.get('total', 0) for s in public_ranking}
for t in timing:
    for c in t.get('commits') or []:
        try:
            ts = dt.datetime.fromisoformat(c)
        except Exception:
            continue
        if WIN_START <= ts <= WIN_END:
            in_window_commits.append((ts, t['slug'], score_by_slug.get(t['slug'], 0)))
total_window_commits = len(in_window_commits)

# AI/stack mentions (case-insensitive substring search over relevant text fields)
def collect_text(s):
    return ' '.join((s.get(k) or '') for k in (
        'Stack & tools', 'How is it agentic / how did you use AI?',
        'What does it do?', 'One-line pitch',
    )).lower()
texts = {s['_slug']: collect_text(s) for s in subs}
def count_mentions(needles):
    if isinstance(needles, str): needles = [needles]
    return sum(1 for t in texts.values() if any(n in t for n in needles))
gemini_n = count_mentions(['gemini', 'google-generative-ai', 'genai'])
openai_n = count_mentions(['openai', 'gpt-', 'gpt ', 'azure openai', 'chatgpt api'])
groq_n = count_mentions(['groq'])
crewai_n = count_mentions(['crewai', 'crew-ai'])
langchain_n = count_mentions(['langchain'])
cursor_n = count_mentions(['cursor'])
lovable_n = count_mentions(['lovable'])
firebase_n = count_mentions(['firebase', 'firestore'])
react_n = count_mentions(['react'])
nextjs_n = count_mentions(['next.js', 'nextjs'])
vite_n = count_mentions(['vite'])
fastapi_n = count_mentions(['fastapi'])

# Tool cloud entries (only ones with at least 2 mentions)
tool_counts = [
    ('Gemini', gemini_n), ('OpenAI / GPT', openai_n), ('Groq', groq_n),
    ('CrewAI', crewai_n), ('LangChain', langchain_n),
    ('Cursor', cursor_n), ('Lovable', lovable_n),
    ('Firebase / Firestore', firebase_n), ('React', react_n),
    ('Next.js', nextjs_n), ('Vite', vite_n), ('FastAPI', fastapi_n),
]
tool_counts = [(n, c) for n, c in tool_counts if c >= 2]
tool_counts.sort(key=lambda x: -x[1])
max_tool = max((c for _, c in tool_counts), default=1)

# Highlights (top 3 podium + four award cards)
top3 = public_ranking[:3]

# Award highlights
def first(predicate, sorted_list):
    for s in sorted_list:
        if predicate(s): return s
    return None

# perfect agentic 10/10 — pick highest among them
perfect_agentic = first(lambda s: s.get('scores', {}).get('agentic') == 10, public_ranking)
# most commits in event window
commit_counts_in_window = Counter(c[1] for c in in_window_commits)
most_commits_slug = max(commit_counts_in_window, key=lambda k: commit_counts_in_window[k]) if commit_counts_in_window else None
def find_record(slug):
    return next((s for s in public_ranking if s['slug'] == slug), None)
most_commits = find_record(most_commits_slug) if most_commits_slug else None
most_commits_n = commit_counts_in_window.get(most_commits_slug, 0) if most_commits_slug else 0

# Top by Data & Insights / Gamified Habit Builder
by_challenge = {}
for s in public_ranking:
    by_challenge.setdefault(s.get('challenge') or '', s)  # first match per challenge after sort = top
data_top = by_challenge.get('Data & Insights') or by_challenge.get('Both')
habit_top = by_challenge.get('Gamified Habit Builder') or by_challenge.get('Both')

# Quotes
quotes = [
    ('Deep', 'turn your real life into the greatest RPG ever played'),
    ('Sarvesh', 'Gamify the grind.'),
    ('Zishan', 'The high-stakes habit tracker where you duel your friends'),
    ('Riyank', 'zero-latency engine reveals hidden stadium biases'),
    ('Soni', 'dopamine loop of Snapchat streaks'),
]

def medal(rank):
    return '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else ''

# ---- Build commit timeline data (for SVG) ----
# Group commits into 10-minute buckets across the event window
bucket_min = 10
n_buckets = int((WIN_END - WIN_START).total_seconds() // 60 // bucket_min) + 1
buckets = [0] * n_buckets
for ts, _, _ in in_window_commits:
    idx = int((ts - WIN_START).total_seconds() // 60 // bucket_min)
    if 0 <= idx < n_buckets:
        buckets[idx] += 1

# Render

def render():
    # Podium HTML — middle (#1) is centered + tallest
    podium_html = ''
    if len(top3) >= 3:
        # Order: #2, #1, #3 for visual stagger
        ordered = [top3[1], top3[0], top3[2]]
        positions = ['second', 'first', 'third']
        for s, pos in zip(ordered, positions):
            podium_html += f'''
        <a class="pod {pos}" href="/scoreboard/" aria-label="View scoreboard">
          <div class="pod-medal">{medal(s["rank"])}</div>
          <div class="pod-rank">#{s["rank"]}</div>
          <div class="pod-name">{html.escape(s.get("name") or "")}</div>
          <div class="pod-title">{html.escape(s.get("title") or "")}</div>
          <div class="pod-score">{s["total"]}<span class="of">/50</span></div>
        </a>'''

    # Tool cloud
    cloud_html = ''
    for name, count in tool_counts:
        size = 0.8 + (count / max_tool) * 1.4  # rem
        cloud_html += f'<span class="tool" style="font-size:{size:.2f}rem">{html.escape(name)} <span class="tool-count">{count}</span></span>'

    # Award cards
    award_cards = []
    if perfect_agentic:
        award_cards.append(('Perfect Agentic 10/10', perfect_agentic.get('name'), perfect_agentic.get('title'),
                             'CrewAI multi-agent · Gemini 1.5 Flash · Groq Llama', '⚡'))
    if most_commits:
        award_cards.append((f'Most Commits · {most_commits_n}', most_commits.get('name'), most_commits.get('title'),
                             f'{most_commits_n} commits in the 5h 49m window — relentless', '🛠'))
    if data_top:
        award_cards.append(('Top in Data & Insights', data_top.get('name'), data_top.get('title'),
                             f'{data_top["total"]}/50 · sharpest insights work', '📊'))
    if habit_top and (not data_top or habit_top['slug'] != data_top['slug']):
        award_cards.append(('Top in Gamified Habit Builder', habit_top.get('name'), habit_top.get('title'),
                             f'{habit_top["total"]}/50 · best habit-loop design', '🎮'))
    awards_html = ''
    for label, name, title, sub, icon in award_cards:
        awards_html += f'''
        <article class="award">
          <div class="award-icon">{icon}</div>
          <div class="award-label">{html.escape(label)}</div>
          <div class="award-title">{html.escape(title or "")}</div>
          <div class="award-name">{html.escape(name or "")}</div>
          <div class="award-sub">{html.escape(sub)}</div>
        </article>'''

    # Quotes carousel
    quotes_html = ''
    for i, (who, q) in enumerate(quotes):
        quotes_html += f'<blockquote class="quote{" active" if i == 0 else ""}" data-i="{i}"><p>“{html.escape(q)}”</p><cite>— {html.escape(who)}</cite></blockquote>'

    # Commit timeline SVG (sparkline-ish bar chart over event window)
    tl_w, tl_h, tl_pad = 720, 100, 30
    max_b = max(buckets) or 1
    bar_w = (tl_w - 2 * tl_pad) / max(len(buckets), 1)
    bars = ''
    for i, n in enumerate(buckets):
        if n == 0: continue
        h_px = (n / max_b) * (tl_h - 30)
        x = tl_pad + i * bar_w
        # color based on time-of-event: earlier = blue, middle = yellow, later = red
        frac = i / max(len(buckets) - 1, 1)
        if frac < 0.4: colour = '#4285F4'
        elif frac < 0.8: colour = '#FBBC04'
        else: colour = '#EA4335'
        bars += f'<rect x="{x:.1f}" y="{tl_h - 18 - h_px:.1f}" width="{max(bar_w-1, 1):.1f}" height="{h_px:.1f}" fill="{colour}" opacity="0.85"><title>{n} commits</title></rect>'

    # Hour labels
    labels = ''
    hours = [(WIN_START + dt.timedelta(hours=h)).strftime('%H:00') for h in range(6)]
    for j, lbl in enumerate(hours):
        x = tl_pad + j * (tl_w - 2*tl_pad) / 5
        labels += f'<text x="{x:.0f}" y="{tl_h - 4}" fill="#9aa0a6" font-size="10">{lbl}</text>'

    challenges_active = total_subs - empty_count
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
    <meta name="theme-color" content="#000000" />
    <title>APL 2026 · The Final Whistle</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@500;700&family=Google+Sans+Text:wght@400;500&display=swap" />
    <link rel="stylesheet" href="/preview/styles.css" />
  </head>
  <body>
    <canvas id="emoji-canvas" aria-hidden="true"></canvas>

    <main class="page">

      <section class="hero">
        <div class="brand-row">
          <span class="dot dot-blue"></span><span class="dot dot-red"></span><span class="dot dot-yellow"></span><span class="dot dot-green"></span>
        </div>
        <h1>That's a wrap.</h1>
        <p class="lead">Build with AI · Agentic Premier League · GDG Baroda</p>
        <p class="tagline"><span class="tag-num">{total_subs}</span> builders · <span class="tag-num">{total_window_commits}</span> commits in <span class="tag-num">5h 49m</span></p>
        <div class="hero-cta">
          <a class="primary" href="/scoreboard/">View full scoreboard →</a>
        </div>
      </section>

      <section class="stats">
        <div class="stat"><div class="stat-num" data-target="{total_subs}">0</div><div class="stat-label">Submissions</div></div>
        <div class="stat"><div class="stat-num" data-target="{total_window_commits}">0</div><div class="stat-label">Commits in window</div></div>
        <div class="stat"><div class="stat-num" data-target="{gemini_n}">0</div><div class="stat-label">Built with Gemini</div></div>
        <div class="stat"><div class="stat-num" data-target="{challenges_active}">0</div><div class="stat-label">Projects shipped</div></div>
      </section>

      <section class="section">
        <h2>The Podium</h2>
        <div class="podium">{podium_html}</div>
        <p class="section-foot">Top three across all 50 submissions. <a href="/scoreboard/">Full ranking →</a></p>
      </section>

      <section class="section">
        <h2>Five-Hour Heartbeat</h2>
        <p class="section-lede">{total_window_commits} commits between 18:00 and 23:49. Each bar = 10 min.</p>
        <svg class="timeline" viewBox="0 0 {tl_w} {tl_h}" preserveAspectRatio="none" aria-label="Commit activity timeline">
          <line x1="{tl_pad}" x2="{tl_w - tl_pad}" y1="{tl_h - 18}" y2="{tl_h - 18}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
          {bars}
          {labels}
        </svg>
      </section>

      <section class="section quotes-section">
        <h2>In Their Words</h2>
        <div class="quotes-stage">{quotes_html}</div>
      </section>

      <section class="section">
        <h2>Award Highlights</h2>
        <div class="awards">{awards_html}</div>
      </section>

      <section class="section">
        <h2>The Stack</h2>
        <div class="tool-cloud">{cloud_html}</div>
      </section>

      <section class="section reactions-section">
        <h2>One More for the Room</h2>
        <p class="section-lede">A leftover from event night. Tap to send.</p>
        <div class="r-grid">
          <button class="rxn" data-glyph="❤️">❤️</button>
          <button class="rxn" data-glyph="🔥">🔥</button>
          <button class="rxn" data-glyph="🎉">🎉</button>
          <button class="rxn" data-glyph="👏">👏</button>
          <button class="rxn" data-glyph="🏏">🏏</button>
          <button class="rxn" data-glyph="6️⃣">6️⃣</button>
          <button class="rxn" data-glyph="4️⃣">4️⃣</button>
          <button class="rxn" data-glyph="😂">😂</button>
          <button class="rxn" data-glyph="😱">😱</button>
          <button class="rxn" data-glyph="🙌">🙌</button>
        </div>
      </section>

      <footer class="foot">
        <p>GDG Baroda · APL 2026</p>
        <p><a href="/scoreboard/">Full scoreboard →</a></p>
      </footer>

    </main>

    <script src="/preview/app.js"></script>
  </body>
</html>
'''

(OUT / 'index.html').write_text(render())
print(f'wrote {OUT / "index.html"}')
print(f'  podium: top 3 from {public_count} public submissions')
print(f'  in-window commits: {total_window_commits}')
print(f'  tool mentions: {tool_counts}')
