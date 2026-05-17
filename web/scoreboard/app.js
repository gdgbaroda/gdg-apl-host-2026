// Scoreboard modal — minimal, no framework.
(function () {
  const data = JSON.parse(document.getElementById('data').textContent);
  const modal = document.getElementById('modal');
  const body = document.getElementById('modal-body');

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
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

    body.innerHTML = `
      <div class="m-head">
        <div class="m-rank">${d.medal} #${d.rank}</div>
        <div class="m-total">${d.total}<span class="of">/50</span></div>
      </div>
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
      </div>

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
