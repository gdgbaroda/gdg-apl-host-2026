#!/usr/bin/env python3
"""Build web/scoreboard/index.html from ranking.json. Reuses the brand styling
from the main APL web site (Google Sans, four brand colors on black)."""
import json, pathlib, html

ROOT = pathlib.Path(__file__).parent
WEB = ROOT.parent / 'web' / 'scoreboard'
WEB.mkdir(parents=True, exist_ok=True)

data = json.loads((ROOT / 'ranking.json').read_text())

# Build cards
cards = []
for s in data:
    rank = s['rank']
    total = s['total']
    sc = s.get('scores', {})
    name = html.escape(s.get('name') or '')
    title = html.escape(s.get('title') or '')
    challenge = html.escape(s.get('challenge') or '')
    reason = html.escape(s.get('reason') or '')
    challenge_class = 'c-blue' if 'Habit' in (s.get('challenge') or '') else 'c-yellow'
    medal = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else ''
    cards.append(f'''
      <article class="card">
        <div class="card-head">
          <div class="rank">{medal} #{rank}</div>
          <div class="total">{total}<span class="of">/50</span></div>
        </div>
        <h2>{title}</h2>
        <div class="meta">
          <span class="name">{name}</span>
          <span class="sep">·</span>
          <span class="challenge {challenge_class}">{challenge}</span>
        </div>
        <p class="reason">{reason}</p>
        <div class="scores">
          <span class="score-pill"><span class="score-label">Agentic</span> <span class="score-val">{sc.get("agentic","?")}</span></span>
          <span class="score-pill"><span class="score-label">Demo</span> <span class="score-val">{sc.get("demo","?")}</span></span>
          <span class="score-pill"><span class="score-label">Quality</span> <span class="score-val">{sc.get("quality","?")}</span></span>
          <span class="score-pill"><span class="score-label">Fit</span> <span class="score-val">{sc.get("fit","?")}</span></span>
          <span class="score-pill"><span class="score-label">Original</span> <span class="score-val">{sc.get("originality","?")}</span></span>
        </div>
      </article>''')

cards_html = '\n'.join(cards)

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
        <p class="subtitle">APL 2026 · {len(data)} submissions scored</p>
        <p class="rubric">Each project scored 1–10 on Agentic AI usage, working demo, code quality, challenge fit, originality — equal weight, max 50.</p>
      </header>
      <section class="cards">
        {cards_html}
      </section>
      <footer class="foot">GDG Baroda · 2026</footer>
    </main>
  </body>
</html>
'''

(WEB / 'index.html').write_text(html_out)
print(f'wrote {WEB / "index.html"} ({len(data)} cards)')
