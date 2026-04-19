// ── Navigation ─────────────────────────────────────────────────────────────────
function navigate(page) {
  showPage(page);
  setActiveNav(page);
}

function showPage(page) {
  document.querySelectorAll('.page').forEach(el => el.classList.remove('active'));
  document.getElementById(`page-${page}`).classList.add('active');
}

function setActiveNav(page) {
  ['gallery', 'practice', 'statistics', 'about'].forEach(p => {
    document.getElementById(`nav-${p}`).classList.toggle('active', p === page);
    document.getElementById(`sidebar-${p}`).classList.toggle('active', p === page);
  });
}

// ── Bootstrap ──────────────────────────────────────────────────────────────────
navigate('practice');
startSession();
