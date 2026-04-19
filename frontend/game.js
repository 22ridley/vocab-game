// ── State ──────────────────────────────────────────────────────────────────────
let sessionWords = [];
let currentIndex = 0;
let score = 0;
let results = []; // { word, isReal, playerAnswer, pointsEarned }
let feedbackActive = false;

// ── Session management ─────────────────────────────────────────────────────────
function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function startSession() {
  sessionWords = shuffle(WORD_POOL).slice(0, NUM_WORDS);
  currentIndex = 0;
  score = 0;
  results = [];
  feedbackActive = false;
  navigate('practice');
  renderWord();
}

// ── Answer handling ────────────────────────────────────────────────────────────
function answer(choice) {
  if (feedbackActive) return;
  feedbackActive = true;

  const w = sessionWords[currentIndex];
  let pointsEarned = 0;

  if (choice === 'recognize' && w.isReal) {
    pointsEarned = CORRECT_WORD;
    renderFeedback('correct-real', w);
  } else if (choice === 'recognize' && !w.isReal) {
    pointsEarned = PENALTY;
    renderFeedback('wrong-fake', w);
  } else if (choice === 'dontrecognize' && !w.isReal) {
    pointsEarned = FAKE_WORD;
    renderFeedback('correct-fake', w);
  } else {
    pointsEarned = 0;
    renderFeedback('wrong-real', w);
  }

  score += pointsEarned;
  results.push({ word: w.word, isReal: w.isReal, playerAnswer: choice, pointsEarned });
  updateScoreDisplay();
}

function nextWord() {
  feedbackActive = false;
  currentIndex++;
  if (currentIndex >= NUM_WORDS) {
    showResults();
  } else {
    renderWord();
  }
}

// ── Rendering ──────────────────────────────────────────────────────────────────
function updateScoreDisplay() {
  document.getElementById('score-display').textContent = score;
}

function updateProgress() {
  const pct = (currentIndex / NUM_WORDS) * 100;
  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('progress-text').textContent = `${currentIndex} / ${NUM_WORDS}`;
}

function renderWord() {
  updateProgress();
  const w = sessionWords[currentIndex];
  document.getElementById('practice-card').innerHTML = `
    <div class="word-display">${w.word}</div>
    <div class="btn-group">
      <button class="btn btn-secondary" onclick="answer('recognize')">Recognize</button>
      <button class="btn btn-primary" onclick="answer('dontrecognize')">Don't Recognize</button>
    </div>
  `;
}

function renderFeedback(type, w) {
  const card = document.getElementById('practice-card');

  if (type === 'correct-real') {
    card.innerHTML = `
      <div class="entry-label">Entry Field</div>
      <div class="status-indicator">
        <span class="status-dot green"></span>
        <span class="status-text green">Correct</span>
      </div>
      <div class="word-display">${w.word}</div>
      <button class="btn btn-primary" onclick="nextWord()">Next Word →</button>
    `;
  } else if (type === 'wrong-fake') {
    card.innerHTML = `
      <div class="entry-label">Entry Field</div>
      <div class="invalid-label">Invalid Term</div>
      <div class="word-display word-invalid">${w.word}</div>
      <button class="btn btn-primary" onclick="nextWord()">Next Word →</button>
    `;
  } else if (type === 'correct-fake') {
    card.innerHTML = `
      <div class="entry-label">Entry Field</div>
      <div class="status-indicator">
        <span class="status-dot green"></span>
        <span class="status-text green">Correctly identified</span>
      </div>
      <div class="word-display">${w.word}</div>
      <button class="btn btn-primary" onclick="nextWord()">Next Word →</button>
    `;
  } else if (type === 'wrong-real') {
    card.innerHTML = `
      <div class="entry-label">Entry Field</div>
      <div class="status-indicator">
        <span class="status-dot orange"></span>
        <span class="status-text orange">That was a real word</span>
      </div>
      <div class="word-display">${w.word}</div>
      <button class="btn btn-primary" onclick="nextWord()">Next Word →</button>
    `;
  }
}

function showResults() {
  updateProgress();
  const correct   = results.filter(r => r.pointsEarned > 0).length;
  const penalties = results.filter(r => r.pointsEarned < 0).length;
  const missed    = results.filter(r => r.pointsEarned === 0 && r.isReal && r.playerAnswer === 'dontrecognize').length;

  document.getElementById('results-card').innerHTML = `
    <div class="results-title">Session Complete</div>
    <div class="results-subtitle">Here's how you did</div>
    <div class="results-score">${score}</div>
    <div class="results-score-label">Final Score</div>
    <div class="results-stats">
      <div class="stat-box">
        <div class="stat-value stat-green">${correct}</div>
        <div class="stat-label">Correct</div>
      </div>
      <div class="stat-box">
        <div class="stat-value stat-red">${penalties}</div>
        <div class="stat-label">Penalized</div>
      </div>
      <div class="stat-box">
        <div class="stat-value">${missed}</div>
        <div class="stat-label">Missed</div>
      </div>
    </div>
    <button class="btn btn-primary" onclick="startSession()">Play Again</button>
  `;

  showPage('results');
  setActiveNav('practice');
}
