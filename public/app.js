// ── Config ────────────────────────────────────────────────────────────────
const MONTHS = [
  { year: 2026, month: 5 },  // June
  { year: 2026, month: 6 },  // July
  { year: 2026, month: 7 },  // August
  { year: 2026, month: 8 },  // September
];

const MONTH_NAMES = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December'
];

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// ── State ──────────────────────────────────────────────────────────────────
let schedule = {};
let currentEditDate = null;

// ── API ────────────────────────────────────────────────────────────────────
async function loadSchedule() {
  try {
    const res = await fetch('/api/schedule');
    schedule = await res.json();
    renderCalendars();
  } catch {
    showToast('Could not load schedule', 'error');
  }
}

async function updateDay(date, name) {
  try {
    const res = await fetch('/api/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, name }),
    });
    const data = await res.json();
    if (!data.success) throw new Error();
    schedule = data.schedule;
    renderCalendars();
    showToast(name ? `Assigned to ${name}` : 'Assignment cleared', 'success');
  } catch {
    showToast('Save failed — please try again', 'error');
  }
}

// ── Render ─────────────────────────────────────────────────────────────────
function renderCalendars() {
  const area = document.getElementById('calendarsArea');
  area.innerHTML = '';
  MONTHS.forEach(({ year, month }) => area.appendChild(buildMonth(year, month)));
}

function buildMonth(year, month) {
  const wrap = document.createElement('div');
  wrap.className = 'month-calendar';

  // Title
  const title = document.createElement('div');
  title.className = 'month-title';
  title.textContent = `${MONTH_NAMES[month]} ${year}`;
  wrap.appendChild(title);

  // Grid
  const grid = document.createElement('div');
  grid.className = 'calendar-grid';

  // Weekday headers
  DAY_NAMES.forEach(d => {
    const h = document.createElement('div');
    h.className = 'weekday-header';
    h.textContent = d;
    grid.appendChild(h);
  });

  // Blank leading cells
  const firstDow = new Date(year, month, 1).getDay();
  for (let i = 0; i < firstDow; i++) {
    const blank = document.createElement('div');
    blank.className = 'day-cell blank-cell';
    grid.appendChild(blank);
  }

  // Day cells
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${pad(month + 1)}-${pad(d)}`;
    const name = schedule[dateStr] || '';

    const cell = document.createElement('div');
    cell.className = `day-cell ${name ? 'filled-cell' : 'empty-cell'}`;
    cell.dataset.date = dateStr;
    cell.setAttribute('title', `${MONTH_NAMES[month]} ${d}${name ? ' — ' + name : ' (click to assign)'}`);
    cell.addEventListener('click', () => openModal(dateStr));

    const num = document.createElement('div');
    num.className = 'cell-num';
    num.textContent = d;
    cell.appendChild(num);

    if (name) {
      const nameDiv = document.createElement('div');
      nameDiv.className = 'cell-name';
      nameDiv.textContent = name;
      cell.appendChild(nameDiv);
    }

    grid.appendChild(cell);
  }

  wrap.appendChild(grid);
  return wrap;
}

function pad(n) { return String(n).padStart(2, '0'); }

// ── Modal ──────────────────────────────────────────────────────────────────
function openModal(dateStr) {
  currentEditDate = dateStr;
  const [y, m, d] = dateStr.split('-');
  document.getElementById('modalDateLabel').textContent =
    `${MONTH_NAMES[parseInt(m) - 1]} ${parseInt(d)}, ${y}`;
  const input = document.getElementById('nameInput');
  input.value = schedule[dateStr] || '';
  document.getElementById('modal').classList.remove('hidden');
  document.getElementById('overlay').classList.remove('hidden');
  setTimeout(() => input.focus(), 50);
}

function closeModal() {
  currentEditDate = null;
  document.getElementById('modal').classList.add('hidden');
  document.getElementById('overlay').classList.add('hidden');
}

function quickSelect(name) {
  document.getElementById('nameInput').value = name;
}

async function saveName() {
  const date = currentEditDate;
  const name = document.getElementById('nameInput').value.trim();
  closeModal();
  if (date) await updateDay(date, name);
}

async function clearName() {
  const date = currentEditDate;
  closeModal();
  if (date) await updateDay(date, '');
}

// Allow Enter key in name input
document.getElementById('nameInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') saveName();
  if (e.key === 'Escape') closeModal();
});

// ── CSV Upload ─────────────────────────────────────────────────────────────
document.getElementById('csvUpload').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async (evt) => {
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: evt.target.result }),
      });
      const data = await res.json();
      if (data.success) {
        schedule = data.schedule;
        renderCalendars();
        showToast('Schedule updated from CSV', 'success');
      } else {
        showToast('CSV error: ' + data.error, 'error');
      }
    } catch {
      showToast('Upload failed', 'error');
    }
  };
  reader.readAsText(file);
  e.target.value = '';
});

// ── Toast ──────────────────────────────────────────────────────────────────
function showToast(msg, type = '') {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.getElementById('toastContainer').appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ── Polling: refresh every 30s to pick up CSV edits on the server ──────────
setInterval(async () => {
  try {
    const res = await fetch('/api/schedule');
    const fresh = await res.json();
    if (JSON.stringify(fresh) !== JSON.stringify(schedule)) {
      schedule = fresh;
      renderCalendars();
      showToast('Schedule refreshed');
    }
  } catch { /* silent fail */ }
}, 30000);

// ── Boot ───────────────────────────────────────────────────────────────────
loadSchedule();
