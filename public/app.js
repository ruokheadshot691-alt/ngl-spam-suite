/**
 * NGL Test Suite — Vercel edition frontend.
 * Stateless: tiap "Send Batch" = 1 HTTP request ke /api/send.
 */
(function () {
  'use strict';

  const $ = (sel) => document.querySelector(sel);
  const els = {
    usernames: $('#usernames'),
    messages: $('#messages'),
    countPerUser: $('#count-per-user'),
    concurrency: $('#concurrency'),
    retry: $('#retry'),
    timeout: $('#timeout'),
    device: $('#device'),
    dryRun: $('#dry-run'),
    btnStart: $('#btn-start'),
    btnClear: $('#btn-clear'),
    btnExportJson: $('#btn-export-json'),
    btnExportCsv: $('#btn-export-csv'),
    btnClearLog: $('#btn-clear-log'),
    log: $('#log'),
    toasts: $('#toasts'),
    connection: $('#connection'),
    themeToggle: $('#theme-toggle'),
    chart: $('#timeline'),
  };

  const statEls = {
    total: document.querySelector('[data-stat="total"]'),
    success: document.querySelector('[data-stat="success"]'),
    failed: document.querySelector('[data-stat="failed"]'),
    elapsed: document.querySelector('[data-stat="elapsed"]'),
  };

  // ------- Chart (inline, no deps) -------
  const chart = (() => {
    const canvas = els.chart;
    const ctx = canvas.getContext('2d');
    let history = [];

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      const w = rect.width || 600;
      const h = 120;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.height = h + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      draw(w, h);
    }

    function draw(w, h) {
      ctx.clearRect(0, 0, w, h);
      const pad = 12;
      const innerW = w - pad * 2;
      const innerH = h - pad * 2;

      ctx.strokeStyle = 'rgba(255,255,255,0.04)';
      for (let i = 0; i <= 3; i++) {
        const y = pad + (innerH / 3) * i;
        ctx.beginPath();
        ctx.moveTo(pad, y);
        ctx.lineTo(pad + innerW, y);
        ctx.stroke();
      }

      if (history.length === 0) {
        ctx.fillStyle = 'rgba(138,138,147,0.6)';
        ctx.font = '11px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.fillText('belum ada batch', w / 2, h / 2);
        return;
      }

      const maxTotal = Math.max(
        1,
        ...history.map((d) => d.success + d.failed)
      );
      const barW = Math.max(3, innerW / history.length - 3);

      history.forEach((d, i) => {
        const x = pad + (innerW / history.length) * i + 2;
        const total = d.success + d.failed;
        if (total === 0) return;
        const sH = (d.success / maxTotal) * innerH;
        const fH = (d.failed / maxTotal) * innerH;

        ctx.fillStyle = '#4ADE80';
        ctx.fillRect(x, pad + innerH - sH, barW, sH);
        ctx.fillStyle = '#F87171';
        ctx.fillRect(x, pad + innerH - sH - fH, barW, fH);
      });
    }

    window.addEventListener('resize', resize);
    resize();

    return {
      push(success, failed) {
        history.push({ success, failed });
        if (history.length > 60) history.shift();
        resize();
      },
      clear() {
        history = [];
        resize();
      },
    };
  })();

  // ------- Utils -------
  const fmtInt = (n) => (n || 0).toLocaleString('en-US');

  function showToast(msg, type = 'info') {
    const el = document.createElement('div');
    el.className = 'toast ' + type;
    el.textContent = msg;
    els.toasts.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transition = 'opacity 200ms';
      setTimeout(() => el.remove(), 220);
    }, 3200);
  }

  function splitLines(str) {
    return (str || '')
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  function appendLog(line, cls = 'info') {
    const ts = new Date().toLocaleTimeString('en-GB');
    const el = document.createElement('div');
    el.className = 'log-line ' + cls;
    el.innerHTML =
      `<span class="ts">${ts}</span>` +
      `<span class="icon">${cls === 'ok' ? '✓' : cls === 'err' ? '✕' : '›'}</span>` +
      `<span class="msg"></span>` +
      `<span class="meta"></span>`;
    el.querySelector('.msg').textContent = line.msg || '';
    el.querySelector('.meta').textContent = line.meta || '';
    els.log.appendChild(el);
    if (els.log.children.length > 800) {
      els.log.removeChild(els.log.firstChild);
    }
    els.log.scrollTop = els.log.scrollHeight;
  }

  function animateNumber(el, from, to, formatter) {
    const start = performance.now();
    const dur = 260;
    const step = (t) => {
      const p = Math.min(1, (t - start) / dur);
      const v = from + (to - from) * (1 - Math.pow(1 - p, 3));
      el.textContent = formatter(v);
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  let cumulative = { total: 0, success: 0, failed: 0 };

  // ------- Actions -------
  async function sendBatch() {
    const usernames = splitLines(els.usernames.value);
    const messages = splitLines(els.messages.value);

    if (usernames.length === 0) {
      showToast('Username wajib diisi', 'error');
      return;
    }
    if (messages.length === 0) {
      messages.push('test message');
    }

    const payload = {
      usernames,
      messages,
      count_per_user: parseInt(els.countPerUser.value, 10) || 1,
      concurrency: parseInt(els.concurrency.value, 10) || 10,
      max_retry: parseInt(els.retry.value, 10) || 0,
      timeout: parseFloat(els.timeout.value) || 10,
      device_strategy: els.device.value,
      dry_run: els.dryRun.checked,
    };

    els.btnStart.disabled = true;
    els.btnStart.textContent = '⏳ Sending…';

    try {
      const res = await fetch('/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();

      // Update stats (cumulative)
      const prev = { ...cumulative };
      cumulative.total += data.total;
      cumulative.success += data.success;
      cumulative.failed += data.failed;

      animateNumber(statEls.total, prev.total, cumulative.total, fmtInt);
      animateNumber(statEls.success, prev.success, cumulative.success, fmtInt);
      animateNumber(statEls.failed, prev.failed, cumulative.failed, fmtInt);
      statEls.elapsed.innerHTML =
        Math.round(data.elapsed_ms) + '<span class="unit">ms</span>';

      chart.push(data.success, data.failed);

      // Log results
      appendLog(
        {
          msg: `batch done — ${data.success}/${data.total} success in ${Math.round(data.elapsed_ms)}ms`,
          meta: `${data.success_rate}%`,
        },
        data.failed === 0 ? 'ok' : 'err'
      );

      // Per result log (max 50)
      data.results.forEach((r) => {
        appendLog(
          {
            msg: `@${r.username} → ${r.status_code} (${Math.round(r.latency_ms)}ms)`,
            meta: `attempts=${r.attempts}${r.error ? ' · ' + r.error : ''}`,
          },
          r.success ? 'ok' : 'err'
        );
      });

      showToast(
        `Batch: ${data.success}/${data.total} success`,
        data.failed === 0 ? 'success' : 'error'
      );
    } catch (e) {
      showToast(e.message, 'error');
      appendLog({ msg: '❌ ' + e.message }, 'err');
    } finally {
      els.btnStart.disabled = false;
      els.btnStart.textContent = '▶ Send Batch';
    }
  }

  function clearAll() {
    els.log.innerHTML = '';
    cumulative = { total: 0, success: 0, failed: 0 };
    ['total', 'success', 'failed'].forEach((k) => {
      statEls[k].textContent = '0';
    });
    statEls.elapsed.innerHTML = '0<span class="unit">ms</span>';
    chart.clear();
    showToast('Cleared');
  }

  function exportJson() {
    const rows = [...els.log.querySelectorAll('.log-line')].map((el) => ({
      ts: el.querySelector('.ts').textContent,
      msg: el.querySelector('.msg').textContent,
      meta: el.querySelector('.meta').textContent,
    }));
    const blob = new Blob([JSON.stringify(rows, null, 2)], {
      type: 'application/json',
    });
    downloadBlob(blob, `ngl-export-${Date.now()}.json`);
  }

  function exportCsv() {
    const rows = [...els.log.querySelectorAll('.log-line')].map((el) => [
      el.querySelector('.ts').textContent,
      el.querySelector('.msg').textContent,
      el.querySelector('.meta').textContent,
    ]);
    const csv = [['ts', 'message', 'meta'], ...rows]
      .map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    downloadBlob(blob, `ngl-export-${Date.now()}.csv`);
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function checkHealth() {
    try {
      const res = await fetch('/api/health');
      if (!res.ok) throw new Error('bad');
      const data = await res.json();
      els.connection.classList.add('on');
      els.connection.classList.remove('off');
      els.connection.querySelector('.conn-text').textContent = 'connected';
      appendLog({ msg: `✅ Connected to ${data.runtime} v${data.version}` }, 'ok');
    } catch {
      els.connection.classList.remove('on');
      els.connection.classList.add('off');
      els.connection.querySelector('.conn-text').textContent = 'offline';
      appendLog({ msg: '❌ API unreachable' }, 'err');
    }
  }

  // ------- Theme -------
  function initTheme() {
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    els.themeToggle.addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-theme');
      const next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    });
  }

  // ------- Bindings -------
  els.btnStart.addEventListener('click', sendBatch);
  els.btnClear.addEventListener('click', clearAll);
  els.btnClearLog.addEventListener('click', () => (els.log.innerHTML = ''));
  els.btnExportJson.addEventListener('click', exportJson);
  els.btnExportCsv.addEventListener('click', exportCsv);

  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') {
      if (e.code === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        sendBatch();
      }
      return;
    }
    if (e.code === 'Escape') clearAll();
  });

  // ------- Init -------
  initTheme();
  checkHealth();
  setInterval(checkHealth, 30000);
  showToast('Ready — Vercel edition');
})();