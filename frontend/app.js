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

async function loadWords() {
  const [realRes, fakeRes] = await Promise.all([
    fetch('./real_words.txt'),
    fetch('./generated_words.txt'),
  ]);
  const [realText, fakeText] = await Promise.all([realRes.text(), fakeRes.text()]);

  const realWords = realText.split('\n').map(w => w.trim()).filter(Boolean)
    .map(w => ({ word: w, isReal: true }));
  const fakeWords = fakeText.split('\n').map(w => w.trim()).filter(Boolean)
    .map(w => ({ word: w, isReal: false }));

  WORD_POOL = [...realWords, ...fakeWords];
  startSession();
}

loadWords();
