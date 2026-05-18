# APL — Agentic Premier League

A reusable hackathon platform from GDG Baroda. Built for a single-evening, IPL-themed _Build with AI_ event but the pieces work for any solo-builder hackathon with a public scoreboard.

**Live example:** [apl.gdgbaroda.com](https://apl.gdgbaroda.com) · [scoreboard](https://apl.gdgbaroda.com/scoreboard/)

---

## What you get

Three deployable pieces that work together (or independently):

| Piece | What it does | Tech |
|---|---|---|
| **`host/`** | Electron app for the projector. Plays live video (Hotstar by default) full-screen, overlays a QR code attendees scan from their phones, renders emoji reactions flying across the screen in real time, and has a F3 "submit results" page with a Google Form QR. | Electron + WebView · ships as DMG / AppImage / deb / win-zip |
| **`api/`** | Cloudflare Worker + Durable Object handling the realtime fan-out (attendees POST emoji → DO buffers and broadcasts to the projector over WebSocket). Cost-weighted rate-limiting, origin allowlist. | Cloudflare Workers · free tier |
| **`web/`** | The attendee-facing site (`apl.gdgbaroda.com`). Single page with challenges, a /scoreboard page with full per-project judging reasoning + commit timelines. | Cloudflare Pages · static HTML/CSS/JS |
| **`pipeline/`** | Post-event scoring pipeline: parse form responses → clone GitHub repos → analyse commit timing → AI vetting agents → roll back to event-deadline state → produce ranked scoreboard. | Python · uses Claude Code agents for vetting |

---

## Quick map

```
gdg-apl/
├── event.config.json     ← the one file you customise for your chapter
├── LICENSE               (MIT)
├── README.md             (this file)
├── docs/
│   └── CHAPTER-GUIDE.md  ← step-by-step setup
├── host/                 ← Electron projector app
├── api/                  ← Cloudflare Worker
├── web/                  ← Cloudflare Pages site
├── pipeline/             ← post-event scoring scripts
└── data/
    └── 2026-baroda/      ← our event's data (sample / reference)
```

---

## Fork it for your chapter

1. **Edit `event.config.json`** — chapter name, event title, challenge briefs, event window, brand colors, URLs.
2. **Replace `data/2026-baroda/`** with `data/<your-chapter-and-year>/` (or update `data_dir` in the config).
3. **Walk the [chapter guide](docs/CHAPTER-GUIDE.md)** for Cloudflare deploys, secrets, and the post-event scoring run.

Full step-by-step in [docs/CHAPTER-GUIDE.md](docs/CHAPTER-GUIDE.md).

---

## What was the event?

A 5h 49m _Build with AI · Agentic Premier League_ hackathon. 50 solo builders pulled up to a hall in Vadodara, an IPL match played live on the projector, and everyone had until 23:49 to ship one project on one of two challenge briefs (Gamified Habit Builder, Data & Insights). We rolled every repo back to its 23:49 state before judging, so participants were scored on what they actually had at deadline — not post-event polish.

The interactivity stack (emoji reactions flying up the projector while attendees tapped them in from their phones) ran on Cloudflare's free tier and stayed live the whole evening.

---

## License

MIT. Take the code, fork the repo, run your own event. Credit appreciated, not required.
