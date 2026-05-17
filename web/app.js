// ---- Challenges (primary content) ----
const CHALLENGES = [
  {
    color: "blue",
    title: "Gamified Habit Builder",
    prompt:
      "Design a platform that uses gamification to help users build and sustain positive habits. Focus on rewards, streaks, and progress tracking to drive engagement.",
  },
  {
    color: "yellow",
    title: "Data & Insights",
    prompt:
      "Design a solution that translates complex match and player data into intuitive and actionable insights for fans. The system should simplify advanced statistics and present them in a way that enhances understanding, decision-making, and overall engagement with the sport.",
  },
];

const challengesEl = document.getElementById("challenges");
CHALLENGES.forEach((c, i) => {
  const card = document.createElement("article");
  card.className = `card card-${c.color}`;
  card.innerHTML = `
    <div class="pill">Challenge ${i + 1}</div>
    <h2>${escapeHtml(c.title)}</h2>
    <p>${escapeHtml(c.prompt)}</p>
  `;
  challengesEl.appendChild(card);
});

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

// ---- Reactions (secondary — just for fun) ----
const API = "https://apl-api.gdgbaroda.com";
const FLUSH_MS = 250;
// One reaction per request — the server rate-limits cost-weighted by n,
// so batching wouldn't buy us anything and would just produce 429s the
// client has to bail on.
const MAX_N_PER_REQ = 1;

const EMOJIS = [
  { id: "heart", glyph: "❤️" },
  { id: "fire",  glyph: "🔥" },
  { id: "party", glyph: "🎉" },
  { id: "clap",  glyph: "👏" },
  { id: "bat",   glyph: "🏏" },
  { id: "six",   glyph: "6️⃣" },
  { id: "four",  glyph: "4️⃣" },
  { id: "laugh", glyph: "😂" },
  { id: "shock", glyph: "😱" },
  { id: "raise", glyph: "🙌" },
];

const grid = document.getElementById("grid");
const status = document.getElementById("status");
const pending = Object.create(null);

// Reactions UI is only rendered during live events. Skip if the DOM is absent.
if (grid && status) {
  for (const e of EMOJIS) {
    const b = document.createElement("button");
    b.className = "btn";
    b.type = "button";
    b.textContent = e.glyph;
    b.setAttribute("aria-label", e.id);
    b.dataset.id = e.id;
    b.addEventListener("pointerdown", () => press(e.id, b), { passive: true });
    grid.appendChild(b);
  }
  setInterval(flush, FLUSH_MS);
}

function press(id, btn) {
  pending[id] = (pending[id] || 0) + 1;
  btn.classList.remove("burst");
  void btn.offsetWidth;
  btn.classList.add("burst");
  if (navigator.vibrate) navigator.vibrate(8);
}

let inFlight = false;
async function flush() {
  if (inFlight) return;
  const keys = Object.keys(pending);
  if (keys.length === 0) return;
  inFlight = true;
  try {
    for (const id of keys) {
      let remaining = pending[id];
      delete pending[id];
      while (remaining > 0) {
        const n = Math.min(MAX_N_PER_REQ, remaining);
        remaining -= n;
        const res = await fetch(`${API}/reactions/send`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ e: id, n }),
          keepalive: true,
        });
        if (res.status === 429) { setStatus("slow down", false); return; }
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
      }
    }
    setStatus("live", true);
  } catch {
    setStatus("offline", false);
  } finally {
    inFlight = false;
  }
}

function setStatus(text, live) {
  if (!status) return;
  status.textContent = text;
  status.classList.toggle("live", !!live);
}
