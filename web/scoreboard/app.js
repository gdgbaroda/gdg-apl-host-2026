// Scoreboard modal — minimal, no framework.
(function () {
  const data = JSON.parse(document.getElementById('data').textContent);
  const modal = document.getElementById('modal');
  const body = document.getElementById('modal-body');

  // Event window — used for the commit timeline shading.
  const WIN_START = new Date('2026-05-16T18:00:00').getTime();
  const WIN_END   = new Date('2026-05-16T23:49:00').getTime();
  const TL_W = 560, TL_H = 60, TL_PAD = 24;

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  function buildTimeline(commits) {
    if (!commits || !commits.length) return '<div class="tl-empty">No commits to plot.</div>';
    const stamps = commits.map(c => new Date(c).getTime()).sort((a, b) => a - b);
    // Axis range = window expanded to include any outliers, capped at ±7 days.
    const minT = Math.min(stamps[0], WIN_START);
    const maxT = Math.max(stamps[stamps.length - 1], WIN_END);
    const pad = (maxT - minT) * 0.04 || 60 * 60 * 1000;
    const lo = minT - pad, hi = maxT + pad;
    const x = (t) => TL_PAD + ((t - lo) / (hi - lo)) * (TL_W - 2 * TL_PAD);

    const winX0 = x(Math.max(WIN_START, lo));
    const winX1 = x(Math.min(WIN_END, hi));

    const ticks = stamps.map(t => {
      const cx = x(t);
      const inWin = t >= WIN_START && t <= WIN_END;
      const colour = inWin ? '#34A853' : '#EA4335';
      return `<line x1="${cx.toFixed(1)}" x2="${cx.toFixed(1)}" y1="14" y2="40" stroke="${colour}" stroke-width="2" stroke-linecap="round"/>`;
    }).join('');

    const fmt = (ms) => {
      const d = new Date(ms);
      return d.getUTCFullYear() < 2026
        ? d.toISOString().slice(0, 10)
        : `${String(d.getDate()).padStart(2,'0')}/${d.getMonth()+1} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    };

    const outsideCount = stamps.filter(t => t < WIN_START || t > WIN_END).length;
    const note = outsideCount
      ? `<div class="tl-note">⚠️ ${outsideCount} commit${outsideCount === 1 ? '' : 's'} outside the event window (red ticks)</div>`
      : `<div class="tl-note">✅ All commits within the event window</div>`;

    return `
      <div class="tl-wrap">
        <svg class="tl-svg" viewBox="0 0 ${TL_W} ${TL_H}" preserveAspectRatio="none" aria-hidden="true">
          <rect x="${winX0}" y="14" width="${winX1 - winX0}" height="26" fill="rgba(52,168,83,0.12)" rx="3"/>
          <line x1="${TL_PAD}" x2="${TL_W - TL_PAD}" y1="27" y2="27" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>
          ${ticks}
          <text x="${TL_PAD}" y="56" fill="#9aa0a6" font-size="10">${fmt(lo)}</text>
          <text x="${TL_W - TL_PAD}" y="56" fill="#9aa0a6" font-size="10" text-anchor="end">${fmt(hi)}</text>
          <text x="${(winX0 + winX1) / 2}" y="10" fill="#34A853" font-size="9" text-anchor="middle" font-weight="700" letter-spacing="0.1em">EVENT WINDOW</text>
        </svg>
        ${note}
      </div>`;
  }

  function linkify(text) {
    // Make bare http(s) URLs clickable in long-form text.
    return escapeHtml(text).replace(/(https?:\/\/[^\s<>"']+)/g, (u) => `<a href="${u}" target="_blank" rel="noopener">${u}</a>`);
  }

  function challengeClass(c) { return /Habit/.test(c) ? 'c-blue' : 'c-yellow'; }

  function renderModal(d) {
    const sc = d.scores || {};
    const links = [];
    if (d.repo_url) links.push(`<a class="link-pill" href="${escapeHtml(d.repo_url)}" target="_blank" rel="noopener">📦 Source</a>`);
    if (d.demo_url) links.push(`<a class="link-pill" href="${escapeHtml(d.demo_url)}" target="_blank" rel="noopener">🟢 Live demo</a>`);

    const demoTag = ({
      '2xx': '🟢 Reachable',
      '404': '⚠️ 404',
      'timeout': '⚠️ Timeout',
      'fail': '⚠️ Failed',
      'video': '🎥 Video',
      'no-url': '— None',
    }[d.demo_check] || '—');

    function field(label, value) {
      if (!value) return '';
      return `<div class="field"><div class="field-label">${escapeHtml(label)}</div><div class="field-value">${linkify(value)}</div></div>`;
    }

    const penaltyHtml = (d.penalty && d.penalty < 0)
      ? `<div class="penalty-note">Timing penalty <strong>${d.penalty}</strong> applied · raw total was ${d.original_total}</div>`
      : '';
    body.innerHTML = `
      <div class="m-head">
        <div class="m-rank">${d.medal} #${d.rank}</div>
        <div class="m-total">${d.total}<span class="of">/50</span></div>
      </div>
      ${penaltyHtml}
      <h2 id="modal-title">${escapeHtml(d.title)}</h2>
      <div class="m-meta">
        <span class="m-name">${escapeHtml(d.name)}</span>
        <span class="sep">·</span>
        <span class="challenge ${challengeClass(d.challenge)}">${escapeHtml(d.challenge)}</span>
      </div>

      ${links.length ? `<div class="link-row">${links.join('')}</div>` : ''}

      <div class="scoregrid">
        <div class="sg"><div class="sg-label">Agentic / AI</div><div class="sg-val">${sc.agentic ?? '?'}/10</div></div>
        <div class="sg"><div class="sg-label">Demo</div><div class="sg-val">${sc.demo ?? '?'}/10</div></div>
        <div class="sg"><div class="sg-label">Code Quality</div><div class="sg-val">${sc.quality ?? '?'}/10</div></div>
        <div class="sg"><div class="sg-label">Challenge Fit</div><div class="sg-val">${sc.fit ?? '?'}/10</div></div>
        <div class="sg"><div class="sg-label">Originality</div><div class="sg-val">${sc.originality ?? '?'}/10</div></div>
      </div>

      <h3>Judge's reasoning</h3>
      <p class="reason">${linkify(d.reason)}</p>

      <div class="evidence">
        <div class="ev"><span class="ev-label">AI evidence</span> <span class="ev-val">${escapeHtml(d.ai_evidence || '—')}</span></div>
        <div class="ev"><span class="ev-label">Demo check</span> <span class="ev-val">${demoTag}</span></div>
        <div class="ev"><span class="ev-label">Commit timing</span> <span class="ev-val">${escapeHtml(d.commit_verdict_label || '—')}</span></div>
        ${d.n_commits != null ? `<div class="ev"><span class="ev-label">Commits</span> <span class="ev-val">${d.n_commits} commit${d.n_commits === 1 ? '' : 's'}${d.first_commit ? ` · first ${escapeHtml(d.first_commit.replace('T', ' '))}` : ''}${d.last_commit && d.last_commit !== d.first_commit ? ` · last ${escapeHtml(d.last_commit.replace('T', ' '))}` : ''}${d.span_pretty && d.span_pretty !== '—' ? ` · span ${escapeHtml(d.span_pretty)}` : ''}</span></div>` : ''}
      </div>

      ${d.commits && d.commits.length ? `<h3>Commit timeline</h3>${buildTimeline(d.commits)}` : ''}

      <h3>From the submission</h3>
      ${field('One-line pitch', d.pitch)}
      ${field('What does it do?', d.what)}
      ${field('How is it agentic / how did you use AI?', d.how_agentic)}
      ${field('Stack & tools', d.stack)}
    `;
  }

  function open(slug) {
    const d = data[slug];
    if (!d) return;
    renderModal(d);
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('no-scroll');
  }
  function close() {
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('no-scroll');
  }

  document.addEventListener('click', (e) => {
    // Anchor clicks inside a card should navigate, not open the modal.
    if (e.target.closest('a.card-link')) return;
    const card = e.target.closest('.card');
    if (card && card.dataset.slug) { open(card.dataset.slug); return; }
    if (e.target.closest('[data-close]')) close();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
    const card = document.activeElement && document.activeElement.closest && document.activeElement.closest('.card');
    if ((e.key === 'Enter' || e.key === ' ') && card && card.dataset.slug) {
      e.preventDefault();
      open(card.dataset.slug);
    }
  });
})();
