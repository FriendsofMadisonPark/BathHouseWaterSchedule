const express = require('express');
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');
const { stringify } = require('csv-stringify/sync');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_DIR = process.env.BATHHOUSE_DATA_DIR || path.join(__dirname, 'data');
const DATA_FILE = process.env.BATHHOUSE_DATA_FILE || path.join(DATA_DIR, 'schedule.csv');

app.use(express.json({ limit: '1mb' }));
app.use(express.static(path.join(__dirname, 'public')));

if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
if (!fs.existsSync(DATA_FILE)) fs.writeFileSync(DATA_FILE, 'date,name\n');

console.log(`Using schedule data file: ${DATA_FILE}`);

function readSchedule() {
  try {
    const content = fs.readFileSync(DATA_FILE, 'utf8');
    const records = parse(content, { columns: true, skip_empty_lines: true });
    const schedule = {};
    records.forEach(r => {
      if (r.date && r.name && r.name.trim()) schedule[r.date] = r.name.trim();
    });
    return schedule;
  } catch {
    return {};
  }
}

function writeSchedule(schedule) {
  const rows = Object.entries(schedule)
    .filter(([, name]) => name && name.trim())
    .map(([date, name]) => ({ date, name: name.trim() }))
    .sort((a, b) => a.date.localeCompare(b.date));
  const content = stringify(rows, { header: true, columns: ['date', 'name'] });
  fs.writeFileSync(DATA_FILE, content);
}

app.get('/api/schedule', (req, res) => {
  res.json(readSchedule());
});

app.post('/api/schedule', (req, res) => {
  const { date, name } = req.body;
  if (!date) return res.status(400).json({ error: 'date required' });
  const schedule = readSchedule();
  if (name && name.trim()) {
    schedule[date] = name.trim();
  } else {
    delete schedule[date];
  }
  writeSchedule(schedule);
  res.json({ success: true, schedule: readSchedule() });
});

app.get('/api/download', (req, res) => {
  res.setHeader('Content-Disposition', 'attachment; filename="watering-schedule.csv"');
  res.setHeader('Content-Type', 'text/csv');
  res.sendFile(DATA_FILE);
});

app.post('/api/upload', (req, res) => {
  try {
    const { content } = req.body;
    if (!content) return res.status(400).json({ error: 'No content provided' });
    const records = parse(content, { columns: true, skip_empty_lines: true });
    const schedule = {};
    records.forEach(r => {
      if (r.date && r.name && r.name.trim()) schedule[r.date] = r.name.trim();
    });
    writeSchedule(schedule);
    res.json({ success: true, schedule: readSchedule() });
  } catch {
    res.status(400).json({ error: 'Invalid CSV format. Expected columns: date, name' });
  }
});

app.listen(PORT, () => {
  console.log(`Madison Park Beach Watering Schedule running on http://localhost:${PORT}`);
});
