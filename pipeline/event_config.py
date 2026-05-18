"""Shared loader for event.config.json + the active data directory.

All pipeline scripts read chapter-specific values from this module instead
of hard-coding them.  Edit `event.config.json` (one file at repo root) to
adapt for a new chapter.
"""
import json, pathlib, datetime as dt

# Repo root = parent of pipeline/
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = json.loads((REPO_ROOT / 'event.config.json').read_text())

# Resolve the data directory (where ranking.json / scores-*.json / etc. live).
DATA_DIR = REPO_ROOT / CONFIG.get('data_dir', 'data/current')
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Event window — parsed naive (timestamps elsewhere are stored naive too)
def _parse_naive(s):
    return dt.datetime.fromisoformat(s.split('+')[0])

EVENT_WINDOW_START = _parse_naive(CONFIG['event']['window']['start'])
EVENT_WINDOW_END   = _parse_naive(CONFIG['event']['window']['end'])

GITHUB_OWNER = CONFIG['github']['owner']
GITHUB_REPO  = CONFIG['github']['repo']
WEB_URL      = CONFIG['urls']['web']
API_URL      = CONFIG['urls']['api']
FORM_URL     = CONFIG['urls']['form']
CHAPTER_NAME = CONFIG['chapter']['name']
EVENT_TITLE  = CONFIG['event']['title']
EVENT_YEAR   = CONFIG['event'].get('year', dt.date.today().year)
CHALLENGES   = CONFIG['challenges']
QUOTES       = CONFIG.get('featured_quotes', [])
VOLUNTEERS   = CONFIG.get('volunteers') or {}
