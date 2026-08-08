# GradTrack — Graduation Project CRM

A small team CRM (team members, task kanban, milestones, per-member file uploads) with a Node.js/Express backend and a SQLite database. Built for a graduation project team to share and use together.

## Stack

- **Backend:** Node.js + Express, using Node's built-in `node:sqlite` (no native build tools required)
- **Frontend:** Single static HTML/CSS/vanilla JS page (`public/index.html`), talks to the backend over a REST API
- **File uploads:** stored on disk under `data/uploads/`, metadata in SQLite
- **No login** — anyone with the URL can view and edit (fine for a small trusted team; see "Adding access control" below if you want to lock it down later)

## Run it locally

Requires Node.js **22.5+** (uses the built-in `node:sqlite` module — no native compilation, so no Visual Studio Build Tools or similar needed).

```bash
npm install
npm start
```

Then open **http://localhost:3000**. Data is stored in `data/gradtrack.db` (created automatically, gitignored). Delete that folder any time to reset to the seed data.

## Deploying to Render (so your team can reach it)

1. **Push this project to a GitHub repo** (see "Publishing to GitHub" below if you haven't yet).
2. Go to [render.com](https://render.com) and sign up / log in (free tier works).
3. **New +** → **Web Service** → connect your GitHub account → pick this repo.
4. Fill in:
   - **Build Command:** `npm install`
   - **Start Command:** `npm start`
   - **Instance Type:** Free (or Starter if you want a persistent disk — see note below)
5. Click **Create Web Service**. Render will build and deploy; you'll get a URL like `https://gradtrack-xyz.onrender.com` to share with your team.

### Important: data persistence on Render's free tier

Render's **free** web services do not guarantee the disk survives across redeploys (a fresh deploy starts with an empty filesystem, wiping `data/gradtrack.db` and all uploaded files). This is fine for a demo/presentation, but if you want the team's data to survive redeploys long-term, either:

- Upgrade to a paid **Starter** instance (~$7/mo) and attach a **Render Disk** mounted at `/opt/render/project/src/data`, or
- Ask me to wire the app up to a free external database (e.g. Turso or a free Postgres like Neon/Supabase) instead of local SQLite — happy to do that if you want real durability without paying for a disk.

## Publishing to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
```

Then create a new repository on github.com (don't initialize it with a README), and:

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

## API overview

| Method | Path | Description |
|---|---|---|
| GET | `/api/data` | Full snapshot: `{ team, tasks, milestones }` |
| POST | `/api/team` | Create team member |
| PUT | `/api/team/:id` | Update team member |
| DELETE | `/api/team/:id` | Remove team member (unassigns their tasks) |
| POST | `/api/team/:id/files` | Upload files (multipart, field name `files`, max 5MB each) |
| DELETE | `/api/files/:id` | Remove an uploaded file |
| POST/PUT/DELETE | `/api/tasks[/:id]` | Task CRUD |
| POST/PUT/DELETE | `/api/milestones[/:id]` | Milestone CRUD (`completed` boolean on PUT) |
| POST | `/api/import` | Replace all data (used by the Import button) |

## Adding access control later

Currently anyone with the link can view/edit everything. If you later want a shared team password or per-member logins, that's a scoped addition to the Express backend (a login route + session cookie) — ask and it can be added without disrupting the rest of the app.
