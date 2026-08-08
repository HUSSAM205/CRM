const path = require('path');
const fs = require('fs');
const { DatabaseSync } = require('node:sqlite');
const crypto = require('crypto');

const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, '..', 'data');
const UPLOAD_DIR = path.join(DATA_DIR, 'uploads');
fs.mkdirSync(UPLOAD_DIR, { recursive: true });

const db = new DatabaseSync(path.join(DATA_DIR, 'gradtrack.db'));
db.exec('PRAGMA journal_mode = WAL');

db.exec(`
  CREATE TABLE IF NOT EXISTS team (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT DEFAULT '',
    email TEXT DEFAULT '',
    phone TEXT DEFAULT ''
  );
  CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL REFERENCES team(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    size INTEGER NOT NULL,
    disk_name TEXT NOT NULL,
    uploaded_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    assignee TEXT REFERENCES team(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'todo',
    priority TEXT NOT NULL DEFAULT 'medium',
    due TEXT DEFAULT ''
  );
  CREATE TABLE IF NOT EXISTS milestones (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT DEFAULT '',
    completed INTEGER NOT NULL DEFAULT 0
  );
`);

function uid(prefix) {
  return prefix + '_' + crypto.randomBytes(6).toString('hex');
}

function addDays(n) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

function seedIfEmpty() {
  const count = db.prepare('SELECT COUNT(*) AS c FROM team').get().c;
  if (count > 0) return;

  const members = [
    { id: uid('m'), name: 'Member One', role: 'Team Lead' },
    { id: uid('m'), name: 'Member Two', role: 'Backend Developer' },
    { id: uid('m'), name: 'Member Three', role: 'Frontend / UI Designer' },
    { id: uid('m'), name: 'Member Four', role: 'Research & Documentation' }
  ];
  const insertMember = db.prepare('INSERT INTO team (id, name, role, email, phone) VALUES (@id, @name, @role, \'\', \'\')');
  members.forEach((m) => insertMember.run(m));

  const [m1, m2, m3, m4] = members.map((m) => m.id);
  const tasks = [
    { id: uid('t'), title: 'Literature review', description: 'Survey related work and prior art.', assignee: m4, status: 'done', priority: 'medium', due: addDays(-20) },
    { id: uid('t'), title: 'Requirements document', description: 'Define scope, users, and success criteria.', assignee: m1, status: 'done', priority: 'high', due: addDays(-12) },
    { id: uid('t'), title: 'System architecture design', description: 'Diagram components and data flow.', assignee: m2, status: 'inprogress', priority: 'high', due: addDays(4) },
    { id: uid('t'), title: 'Database schema', description: 'Model entities and relationships.', assignee: m2, status: 'todo', priority: 'medium', due: addDays(9) },
    { id: uid('t'), title: 'UI wireframes & prototype', description: 'Low-fi then hi-fi screens for core flows.', assignee: m3, status: 'inprogress', priority: 'medium', due: addDays(6) },
    { id: uid('t'), title: 'Write chapter 3 — Methodology', description: '', assignee: m4, status: 'todo', priority: 'low', due: addDays(15) },
    { id: uid('t'), title: 'Prepare progress presentation', description: 'Slides for supervisor check-in.', assignee: m1, status: 'todo', priority: 'high', due: addDays(2) }
  ];
  const insertTask = db.prepare('INSERT INTO tasks (id, title, description, assignee, status, priority, due) VALUES (@id, @title, @description, @assignee, @status, @priority, @due)');
  tasks.forEach((t) => insertTask.run(t));

  const milestones = [
    { id: uid('ms'), title: 'Proposal submission', date: addDays(-30), description: 'Submit project proposal to committee.', completed: 1 },
    { id: uid('ms'), title: 'Midterm progress review', date: addDays(-5), description: 'Demo current progress to supervisor.', completed: 1 },
    { id: uid('ms'), title: 'System implementation complete', date: addDays(20), description: 'Feature-complete build ready for testing.', completed: 0 },
    { id: uid('ms'), title: 'Final report submission', date: addDays(45), description: 'Submit full written thesis/report.', completed: 0 },
    { id: uid('ms'), title: 'Thesis defense', date: addDays(60), description: 'Present and defend in front of committee.', completed: 0 }
  ];
  const insertMilestone = db.prepare('INSERT INTO milestones (id, title, date, description, completed) VALUES (@id, @title, @date, @description, @completed)');
  milestones.forEach((m) => insertMilestone.run(m));
}

seedIfEmpty();

module.exports = { db, uid, UPLOAD_DIR };
