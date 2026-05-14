// ── Watchlist Toggle (AJAX) ──────────────────────────────────────
function getCookie(name) {
  let v = null;
  document.cookie.split(';').forEach(c => {
    const [k, val] = c.trim().split('=');
    if (k === name) v = decodeURIComponent(val);
  });
  return v;
}

document.addEventListener('click', function(e) {
  const btn = e.target.closest('.watchlist-btn');
  if (!btn) return;
  const pk = btn.dataset.pk;
  if (!pk) return;
  e.preventDefault();
  e.stopPropagation();
  fetch(`/watchlist/toggle/${pk}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' }
  })
  .then(r => r.json())
  .then(data => {
    if (btn.classList.contains('btn-action-primary')) {
      if (data.status === 'added') {
        btn.textContent = '✓ In Watchlist';
        btn.classList.add('in-list');
      } else {
        btn.textContent = '+ Add to Watchlist';
        btn.classList.remove('in-list');
      }
    }
    showToast(data.message || (data.status === 'added' ? '✓ Added to watchlist' : 'Removed from watchlist'));
  })
  .catch(() => showToast('Please log in to use watchlist', 'error'));
});

// Mark watched toggle
document.addEventListener('click', function(e) {
  const btn = e.target.closest('.watched-btn');
  if (!btn) return;
  const pk = btn.dataset.pk;
  fetch(`/watchlist/watched/${pk}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'added') {
      btn.textContent = '✓ Watched';
      btn.classList.add('watched');
    } else {
      btn.textContent = 'Mark as Watched';
      btn.classList.remove('watched');
    }
    showToast(data.status === 'added' ? '✓ Marked as watched' : 'Removed from watched');
  });
});

// Remove from watchlist (profile page)
function removeWatchlistRow(btn, pk) {
  const row = document.getElementById('wl-' + pk);
  fetch(`/watchlist/toggle/${pk}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  })
  .then(r => r.json())
  .then(() => {
    if (row) { row.style.opacity = '0'; row.style.transition = 'opacity .3s'; setTimeout(() => row.remove(), 300); }
    showToast('Removed from watchlist');
  });
}

// ── Toast Notification ───────────────────────────────────────────
function showToast(msg, type='success') {
  const t = document.createElement('div');
  t.className = `toast-notify toast-${type}`;
  t.textContent = msg;
  Object.assign(t.style, {
    position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999,
    background: type === 'error' ? '#c62828' : '#1b5e20',
    color: '#fff', padding: '10px 18px', borderRadius: '8px',
    fontSize: '13px', fontFamily: 'DM Sans, sans-serif',
    boxShadow: '0 4px 20px rgba(0,0,0,.4)', opacity: '0', transition: 'opacity .3s'
  });
  document.body.appendChild(t);
  setTimeout(() => t.style.opacity = '1', 10);
  setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 2500);
}
// ── TRAILER PLAYER ───────────────────────────────────────────────

function openTrailer(movieTitle, youtubeKey) {
  const modal   = document.getElementById('trailerModal');
  const content = document.getElementById('trailerContent');

  // Show the modal first
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  if (youtubeKey && youtubeKey.trim() !== '') {
    // We have saved YouTube key → play directly
    content.innerHTML = `
      <iframe
        src="https://www.youtube.com/embed/${youtubeKey}?autoplay=1&rel=0"
        allow="autoplay; encrypted-media; fullscreen"
        allowfullscreen>
      </iframe>`;

  } else {
    // No saved key → show search options
    const query   = encodeURIComponent(movieTitle + ' official trailer');
    const ytSearch = `https://www.youtube.com/results?search_query=${query}`;

    content.innerHTML = `
      <div style="
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
        height:100%;
        gap:20px;
        padding:30px;
        text-align:center;
      ">
        <div style="font-size:48px;">🎬</div>
        <div style="font-size:18px; font-weight:600; color:#fff;">
          ${movieTitle}
        </div>
        <div style="font-size:13px; color:#aaa;">
          Click below to watch the official trailer on YouTube
        </div>
        
          href="${ytSearch}"
          target="_blank"
          onclick="closeTrailerBtn()"
          style="
            display:inline-flex;
            align-items:center;
            gap:10px;
            padding:14px 28px;
            background:#FF0000;
            color:#fff;
            border-radius:10px;
            text-decoration:none;
            font-size:15px;
            font-weight:600;
          ">
          ▶ Watch Trailer on YouTube
        </a>
        <div style="font-size:12px; color:#666;">
          Opens YouTube search for "${movieTitle} official trailer"
        </div>
      </div>`;
  }
}

function closeTrailer(event) {
  // Close only if user clicked the dark background
  if (event.target === document.getElementById('trailerModal')) {
    closeTrailerBtn();
  }
}

function closeTrailerBtn() {
  const modal   = document.getElementById('trailerModal');
  const content = document.getElementById('trailerContent');
  modal.style.display = 'none';
  content.innerHTML   = '';
  document.body.style.overflow = '';
}

// Close with Escape key
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeTrailerBtn();
});