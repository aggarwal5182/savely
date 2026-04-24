/* ── Savely — main.js ──────────────────────────────────────────────────── */

const urlInput   = document.getElementById('urlInput');
const fetchBtn   = document.getElementById('fetchBtn');
const statusMsg  = document.getElementById('statusMsg');
const resultBox  = document.getElementById('resultBox');
const resultThumb  = document.getElementById('resultThumb');
const resultTitle  = document.getElementById('resultTitle');
const resultAuthor = document.getElementById('resultAuthor');
const resultDuration = document.getElementById('resultDuration');
const qualGrid   = document.getElementById('qualGrid');

// ── tab switching ─────────────────────────────────────────────────────────
const tabPlaceholders = {
  video: 'Paste Instagram / TikTok / YouTube video link…',
  photo: 'Paste Instagram photo post link…',
  reels: 'Paste Instagram Reels link…',
  story: 'Paste Instagram Story link…',
  audio: 'Paste any video link to extract audio…',
};

document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    urlInput.placeholder = tabPlaceholders[tab.dataset.tab] || 'Paste link here…';
    reset();
  });
});

// ── helpers ───────────────────────────────────────────────────────────────
function setStatus(msg, cls = '') {
  statusMsg.textContent = msg;
  statusMsg.className = 'status-msg' + (cls ? ' ' + cls : '');
}

function reset() {
  resultBox.classList.remove('show');
  setStatus('');
  qualGrid.innerHTML = '';
}

function fmtDuration(secs) {
  if (!secs) return '';
  const m = Math.floor(secs / 60);
  const s = String(Math.floor(secs % 60)).padStart(2, '0');
  return `${m}:${s}`;
}

// ── fetch info ────────────────────────────────────────────────────────────
fetchBtn.addEventListener('click', fetchInfo);
urlInput.addEventListener('keydown', e => { if (e.key === 'Enter') fetchInfo(); });

async function fetchInfo() {
  const url = urlInput.value.trim();
  if (!url) { setStatus('Please paste a link first.', 'error'); return; }
  if (!url.startsWith('http')) { setStatus('URL must start with https://', 'error'); return; }

  reset();
  fetchBtn.disabled = true;
  setStatus('Fetching media info…', 'loading');

  try {
    const res  = await fetch('/api/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();

    if (!res.ok) {
      setStatus(data.error || 'Could not fetch info. Check the link and try again.', 'error');
      return;
    }

    // populate result card
    resultThumb.src = data.thumbnail || '';
    resultThumb.style.display = data.thumbnail ? 'block' : 'none';
    resultTitle.textContent  = data.title   || 'Unknown title';
    resultAuthor.textContent = data.uploader ? `@${data.uploader} · ${data.platform}` : data.platform;
    resultDuration.textContent = data.duration ? `Duration: ${fmtDuration(data.duration)}` : '';

    // build quality buttons
    qualGrid.innerHTML = '';
    (data.qualities || []).forEach(q => {
      const btn = document.createElement('button');
      btn.className = 'qual-btn';
      btn.innerHTML = `<span class="qual-name">${q.label}</span>
                       <span class="qual-detail">${q.ext.toUpperCase()} · tap to download</span>`;
      btn.addEventListener('click', () => startDownload(url, q));
      qualGrid.appendChild(btn);
    });

    resultBox.classList.add('show');
    setStatus('');
  } catch (err) {
    setStatus('Network error — please try again.', 'error');
  } finally {
    fetchBtn.disabled = false;
  }
}

// ── download ──────────────────────────────────────────────────────────────
async function startDownload(url, quality) {
  // disable all quality buttons while downloading
  const allBtns = qualGrid.querySelectorAll('.qual-btn');
  allBtns.forEach(b => { b.disabled = true; });
  setStatus(`Preparing ${quality.label} download…`, 'loading');

  try {
    const res  = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, quality: quality.quality }),
    });
    const data = await res.json();

    if (!res.ok) {
      setStatus(data.error || 'Download failed.', 'error');
      return;
    }

    // trigger browser download
    const a = document.createElement('a');
    a.href = data.download_url;
    a.download = data.filename || 'download';
    document.body.appendChild(a);
    a.click();
    a.remove();

    setStatus(
      `✓ Download started — ${data.size_mb} MB · ${quality.label}`,
      'success'
    );
  } catch (err) {
    setStatus('Network error during download.', 'error');
  } finally {
    allBtns.forEach(b => { b.disabled = false; });
  }
}

// ── FAQ accordion ─────────────────────────────────────────────────────────
document.querySelectorAll('.faq-item').forEach(item => {
  item.addEventListener('click', () => item.classList.toggle('open'));
});
