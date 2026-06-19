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
  fetch('/watchlist/toggle/' + pk + '/', {
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
        btn.textContent = '+ Watchlist';
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
  fetch('/watchlist/watched/' + pk + '/', {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'added') {
      btn.textContent = '✓ Watched';
      btn.classList.add('watched');
    } else {
      btn.textContent = 'Mark Watched';
      btn.classList.remove('watched');
    }
    showToast(data.status === 'added' ? '✓ Marked as watched' : 'Removed from watched');
  });
});

// Remove from watchlist (profile page)
function removeWatchlistRow(btn, pk) {
  const row = document.getElementById('wl-' + pk);
  fetch('/watchlist/toggle/' + pk + '/', {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  })
  .then(r => r.json())
  .then(() => {
    if (row) {
      row.style.opacity = '0';
      row.style.transition = 'opacity .3s';
      setTimeout(() => row.remove(), 300);
    }
    showToast('Removed from watchlist');
  });
}

// ── Toast Notification ───────────────────────────────────────────
function showToast(msg, type) {
  type = type || 'success';
  const t = document.createElement('div');
  t.textContent = msg;
  Object.assign(t.style, {
    position: 'fixed',
    bottom: '24px',
    right: '24px',
    zIndex: 9999,
    background: type === 'error' ? '#c62828' : '#1b5e20',
    color: '#fff',
    padding: '10px 18px',
    borderRadius: '8px',
    fontSize: '13px',
    fontFamily: 'DM Sans, sans-serif',
    boxShadow: '0 4px 20px rgba(0,0,0,.4)',
    opacity: '0',
    transition: 'opacity .3s'
  });
  document.body.appendChild(t);
  setTimeout(() => { t.style.opacity = '1'; }, 10);
  setTimeout(() => {
    t.style.opacity = '0';
    setTimeout(() => t.remove(), 300);
  }, 2500);
}