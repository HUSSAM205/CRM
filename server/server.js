const path = require('path');
const fs = require('fs');
const express = require('express');
const multer = require('multer');
const { db, uid, UPLOAD_DIR } = require('./db');

db.exec('PRAGMA foreign_keys = ON');

const app = express();
const PORT = process.env.PORT || 3000;
const MAX_FILE_BYTES = 5 * 1024 * 1024;

app.use(express.json());

function sanitizeName(name) {
  return String(name).replace(/[^a-zA-Z0-9.\-_]+/g, '_').slice(-120);
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOAD_DIR),
  filename: (req, file, cb) => {
    const id = uid('f');
    file._genId = id;
    cb(null, id + '__' + sanitizeName(file.originalname));
  }
});
const upload = multer({ storage, limits: { fileSize: MAX_FILE_BYTES } });

/* ---------- Helpers ---------- */
function getFullData() {
  const team = db.prepare('SELECT * FROM team ORDER BY rowid').all();
  const files = db.prepare('SELECT * FROM files ORDER BY uploaded_at').all();
  const tasks = db.prepare('SELECT * FROM tasks ORDER BY rowid').all();
  const milestones = db.prepare('SELECT * FROM milestones ORDER BY rowid').all();

  const filesByMember = {};
  files.forEach((f) => {
    if (!filesByMember[f.member_id]) filesByMember[f.member_id] = [];
    filesByMember[f.member_id].push({
      id: f.id,
      name: f.name,
      size: f.size,
      url: '/uploads/' + f.disk_name
    });
  });
  team.forEach((m) => { m.files = filesByMember[m.id] || []; });
  milestones.forEach((m) => { m.completed = !!m.completed; });

  return { team, tasks, milestones };
}

/* ---------- Data snapshot ---------- */
app.get('/api/data', (req, res) => {
  res.json(getFullData());
});

app.post('/api/import', (req, res) => {
  const { team, tasks, milestones } = req.body || {};
  if (!Array.isArray(team) || !Array.isArray(tasks) || !Array.isArray(milestones)) {
    return res.status(400).json({ error: 'Invalid import shape' });
  }
  const files = db.prepare('SELECT disk_name FROM files').all();
  db.exec('BEGIN');
  try {
    db.prepare('DELETE FROM files').run();
    db.prepare('DELETE FROM tasks').run();
    db.prepare('DELETE FROM milestones').run();
    db.prepare('DELETE FROM team').run();
    const insM = db.prepare('INSERT INTO team (id, name, role, email, phone) VALUES (@id, @name, @role, @email, @phone)');
    team.forEach((m) => insM.run({
      id: m.id || uid('m'), name: m.name || '', role: m.role || '', email: m.email || '', phone: m.phone || ''
    }));
    const insT = db.prepare('INSERT INTO tasks (id, title, description, assignee, status, priority, due) VALUES (@id, @title, @description, @assignee, @status, @priority, @due)');
    tasks.forEach((t) => insT.run({
      id: t.id || uid('t'), title: t.title || '', description: t.description || '', assignee: t.assignee || null,
      status: t.status || 'todo', priority: t.priority || 'medium', due: t.due || ''
    }));
    const insMs = db.prepare('INSERT INTO milestones (id, title, date, description, completed) VALUES (@id, @title, @date, @description, @completed)');
    milestones.forEach((m) => insMs.run({
      id: m.id || uid('ms'), title: m.title || '', date: m.date || '', description: m.description || '', completed: m.completed ? 1 : 0
    }));
    db.exec('COMMIT');
  } catch (err) {
    db.exec('ROLLBACK');
    throw err;
  }
  files.forEach((f) => {
    fs.unlink(path.join(UPLOAD_DIR, f.disk_name), () => {});
  });
  res.json(getFullData());
});

/* ---------- Team ---------- */
app.post('/api/team', (req, res) => {
  const { name, role, email, phone } = req.body || {};
  if (!name || !String(name).trim()) return res.status(400).json({ error: 'Name is required' });
  const member = { id: uid('m'), name: String(name).trim(), role: role || '', email: email || '', phone: phone || '' };
  db.prepare('INSERT INTO team (id, name, role, email, phone) VALUES (@id, @name, @role, @email, @phone)').run(member);
  member.files = [];
  res.status(201).json(member);
});

app.put('/api/team/:id', (req, res) => {
  const { name, role, email, phone } = req.body || {};
  if (!name || !String(name).trim()) return res.status(400).json({ error: 'Name is required' });
  const info = db.prepare('UPDATE team SET name=?, role=?, email=?, phone=? WHERE id=?')
    .run(String(name).trim(), role || '', email || '', phone || '', req.params.id);
  if (info.changes === 0) return res.status(404).json({ error: 'Not found' });
  res.json(db.prepare('SELECT * FROM team WHERE id=?').get(req.params.id));
});

app.delete('/api/team/:id', (req, res) => {
  const files = db.prepare('SELECT disk_name FROM files WHERE member_id=?').all(req.params.id);
  const info = db.prepare('DELETE FROM team WHERE id=?').run(req.params.id);
  if (info.changes === 0) return res.status(404).json({ error: 'Not found' });
  db.prepare('UPDATE tasks SET assignee=NULL WHERE assignee=?').run(req.params.id);
  files.forEach((f) => fs.unlink(path.join(UPLOAD_DIR, f.disk_name), () => {}));
  res.status(204).end();
});

/* ---------- Member files ---------- */
app.post('/api/team/:id/files', upload.array('files', 10), (req, res) => {
  const member = db.prepare('SELECT id FROM team WHERE id=?').get(req.params.id);
  if (!member) return res.status(404).json({ error: 'Member not found' });
  const insert = db.prepare('INSERT INTO files (id, member_id, name, size, disk_name, uploaded_at) VALUES (@id, @member_id, @name, @size, @disk_name, @uploaded_at)');
  const created = (req.files || []).map((f) => {
    const rec = {
      id: f._genId, member_id: req.params.id, name: f.originalname, size: f.size,
      disk_name: f.filename, uploaded_at: new Date().toISOString()
    };
    insert.run(rec);
    return { id: rec.id, name: rec.name, size: rec.size, url: '/uploads/' + rec.disk_name };
  });
  res.status(201).json(created);
});

app.delete('/api/files/:id', (req, res) => {
  const file = db.prepare('SELECT * FROM files WHERE id=?').get(req.params.id);
  if (!file) return res.status(404).json({ error: 'Not found' });
  db.prepare('DELETE FROM files WHERE id=?').run(req.params.id);
  fs.unlink(path.join(UPLOAD_DIR, file.disk_name), () => {});
  res.status(204).end();
});

/* ---------- Tasks ---------- */
app.post('/api/tasks', (req, res) => {
  const { title, description, assignee, status, priority, due } = req.body || {};
  if (!title || !String(title).trim()) return res.status(400).json({ error: 'Title is required' });
  const task = {
    id: uid('t'), title: String(title).trim(), description: description || '', assignee: assignee || null,
    status: status || 'todo', priority: priority || 'medium', due: due || ''
  };
  db.prepare('INSERT INTO tasks (id, title, description, assignee, status, priority, due) VALUES (@id, @title, @description, @assignee, @status, @priority, @due)').run(task);
  res.status(201).json(task);
});

app.put('/api/tasks/:id', (req, res) => {
  const existing = db.prepare('SELECT * FROM tasks WHERE id=?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: 'Not found' });
  const { title, description, assignee, status, priority, due } = req.body || {};
  const next = {
    title: title != null ? String(title).trim() : existing.title,
    description: description != null ? description : existing.description,
    assignee: assignee !== undefined ? assignee : existing.assignee,
    status: status || existing.status,
    priority: priority || existing.priority,
    due: due != null ? due : existing.due
  };
  db.prepare('UPDATE tasks SET title=?, description=?, assignee=?, status=?, priority=?, due=? WHERE id=?')
    .run(next.title, next.description, next.assignee, next.status, next.priority, next.due, req.params.id);
  res.json(db.prepare('SELECT * FROM tasks WHERE id=?').get(req.params.id));
});

app.delete('/api/tasks/:id', (req, res) => {
  const info = db.prepare('DELETE FROM tasks WHERE id=?').run(req.params.id);
  if (info.changes === 0) return res.status(404).json({ error: 'Not found' });
  res.status(204).end();
});

/* ---------- Milestones ---------- */
app.post('/api/milestones', (req, res) => {
  const { title, date, description } = req.body || {};
  if (!title || !String(title).trim()) return res.status(400).json({ error: 'Title is required' });
  if (!date) return res.status(400).json({ error: 'Date is required' });
  const milestone = { id: uid('ms'), title: String(title).trim(), date, description: description || '', completed: 0 };
  db.prepare('INSERT INTO milestones (id, title, date, description, completed) VALUES (@id, @title, @date, @description, @completed)').run(milestone);
  milestone.completed = false;
  res.status(201).json(milestone);
});

app.put('/api/milestones/:id', (req, res) => {
  const existing = db.prepare('SELECT * FROM milestones WHERE id=?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: 'Not found' });
  const { title, date, description, completed } = req.body || {};
  const next = {
    title: title != null ? String(title).trim() : existing.title,
    date: date || existing.date,
    description: description != null ? description : existing.description,
    completed: completed !== undefined ? (completed ? 1 : 0) : existing.completed
  };
  db.prepare('UPDATE milestones SET title=?, date=?, description=?, completed=? WHERE id=?')
    .run(next.title, next.date, next.description, next.completed, req.params.id);
  const row = db.prepare('SELECT * FROM milestones WHERE id=?').get(req.params.id);
  row.completed = !!row.completed;
  res.json(row);
});

app.delete('/api/milestones/:id', (req, res) => {
  const info = db.prepare('DELETE FROM milestones WHERE id=?').run(req.params.id);
  if (info.changes === 0) return res.status(404).json({ error: 'Not found' });
  res.status(204).end();
});

/* ---------- Static assets ---------- */
app.use('/uploads', express.static(UPLOAD_DIR));
app.use(express.static(path.join(__dirname, '..', 'public')));

app.use((err, req, res, next) => {
  if (err && err.code === 'LIMIT_FILE_SIZE') {
    return res.status(413).json({ error: 'File too large (max 5MB)' });
  }
  console.error(err);
  res.status(500).json({ error: 'Server error' });
});

app.listen(PORT, () => {
  console.log('GradTrack server running on http://localhost:' + PORT);
});
