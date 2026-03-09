# 📋 Development Plan — Board Game Night Planner

This document outlines the full development roadmap, from a local Python MVP to a production Kubernetes deployment.

---

## 🏗 Project Structure

```
cal/
├── Home.py                   # Entry point (redirects to Vote)
├── pages/                    # Streamlit multi-page app
│   ├── 01_🗳️_Vote.py        # User voting page (entry)
│   ├── 02_➕_Add_Game.py     # Add game manually
│   ├── 03_📋_Current_Games.py # View/edit/delete games
│   ├── 04_📊_Results.py     # Scores & table assignments
│   ├── 05_⚙️_Admin.py       # Import XLSX, algorithms, physical tables
│   └── 06_❓_Help.py        # How it works
├── db/
│   ├── database.py           # Database connection & session
│   ├── models.py             # SQLAlchemy models
│   ├── import_games.py       # XLSX import logic
│   └── seed.py               # Optional: seed data for testing
├── logic/
│   ├── scoring.py            # Game scoring & selection
│   └── assignment.py         # Player-to-table assignment
├── ui/
│   └── theme_toggle.py       # Light/dark theme
├── alembic/                  # Database migrations
├── k8s/                      # Kubernetes manifests
├── docker-compose.yml
├── Dockerfile
├── README.md
├── DEVELOPMENT_PLAN.md
└── LICENSE
```

---

## 🎯 Milestone 1: Local Python App (Streamlit MVP)

**Goal:** A fully working Streamlit app running locally, connected to PostgreSQL via Docker Compose.

### 1.1 — Project Setup

- [ ] Initialize Python virtual environment
- [x] Create `requirements.txt` with initial dependencies:
  ```
  streamlit
  sqlalchemy
  psycopg2-binary
  alembic
  python-dotenv
  ```
- [x] Create `.env.example` with:
  ```
  DATABASE_URL=postgresql://cal:cal@localhost:5432/cal
  ```
- [x] Create project directory structure (as shown above)

### 1.2 — Local PostgreSQL (Docker Compose)

- [x] Create `docker-compose.yml` with PostgreSQL service:
  ```yaml
  services:
    db:
      image: postgres:16
      environment:
        POSTGRES_USER: cal
        POSTGRES_PASSWORD: cal
        POSTGRES_DB: cal
      ports:
        - "5432:5432"
      volumes:
        - pgdata:/var/lib/postgresql/data
  volumes:
    pgdata:
  ```
- [ ] Verify connection with `psql` or a DB client

### 1.3 — Database Models & Migrations

- [x] Define SQLAlchemy models in `db/models.py`:
  - `User` — id, name, submitted_at, assigned_table_id
  - `Game` — id, bgg_id, title, min_players, max_players, is_selected
  - `Table` — id, name, capacity, sort_order (physical tables)
  - `TableInstance` — id, table_id, game_id (links physical table to game)
  - `Preference` — id, user_id, game_id, rank
- [x] Set up Alembic for migrations (`alembic init alembic`)
- [x] Generate and run initial migration
- [x] Create `db/database.py` with engine, session factory, and connection helper

### 1.4 — Game Management (split across pages)

- [x] **Add Game** (`pages/02_➕_Add_Game.py`) — add new game (title, min/max players)
- [x] **Current Games** (`pages/03_📋_Current_Games.py`) — view all games, edit, delete
- [x] **Import from XLSX** — in Admin; supports BGG format, multi-sheet, Kocie-gierce

### 1.5 — User Voting Page

- [x] Voting page (`pages/01_🗳️_Vote.py`) with:
  - User enters their name
  - Selects 1st, 2nd, and 3rd choice from dropdown (no duplicates allowed)
  - Submit button stores preferences with timestamp
  - Confirmation message after submission
  - Prevent duplicate submissions (same user name)

### 1.6 — Scoring Algorithm

- [x] Implement in `logic/scoring.py`:
  - Calculate weighted score per game: `3×n1 + 2×n2 + 1×n3`
  - Determine which games meet the threshold and min_players requirement
  - Mark qualifying games as `is_selected = True`
- [x] Display scores on results page (`pages/04_📊_Results.py`)

### 1.7 — Assignment Algorithm

- [x] Implement in `logic/assignment.py`:
  - Sort users by `submitted_at` (ascending — first-come, first-served)
  - For each user, try to assign to their 1st choice table
  - If full, try 2nd choice, then 3rd choice
  - If multiple table instances exist for a game, fill them in order
  - Flag unassigned users
- [x] Admin triggers assignment from the admin page
- [x] Display assignments on results page

### 1.8 — Physical Tables & Game Assignment

- [x] **Physical tables** — Admin defines tables (name, capacity, e.g. 2×6, 2×4 seats)
- [x] **Calculate Scores & Select Games** — selects games by votes, auto-creates `TableInstance` per physical table
- [x] **Assign Games to Tables** — admin assigns selected game to each physical table
- [x] Edit/delete physical tables; display player count per table

### 1.9 — Fallback UI for Unassigned Players

- [x] On the voting/results page, detect if the current user is unassigned
- [x] Show a special view with only tables that have open seats
- [x] User picks a table manually → updates their `assigned_table_id`

### 1.10 — Admin Dashboard

- [x] Summary view showing:
  - Total users, total votes submitted
  - Game scores (ranked)
  - Table assignments (who is where)
  - List of unassigned users
  - Button to run/re-run the assignment algorithm
  - Button to reset all assignments (for re-running)

---

## 🐳 Milestone 2: Dockerize

**Goal:** The entire stack (app + database) runs in Docker with a single command.

### 2.1 — Dockerfile

- [x] Create multi-stage `Dockerfile` for the Streamlit app:
  ```dockerfile
  FROM python:3.12-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 8501
  CMD ["sh", "-c", "alembic upgrade head && exec streamlit run Home.py --server.address=0.0.0.0"]
  ```

### 2.2 — Docker Compose (Full Stack)

- [x] Update `docker-compose.yml` to include both services:
  ```yaml
  services:
    app:
      build: .
      ports:
        - "8501:8501"
      environment:
        DATABASE_URL: postgresql://cal:cal@db:5432/cal
      depends_on:
        db:
          condition: service_healthy
    db:
      image: postgres:16
      environment:
        POSTGRES_USER: cal
        POSTGRES_PASSWORD: cal
        POSTGRES_DB: cal
      ports:
        - "5432:5432"
      volumes:
        - pgdata:/var/lib/postgresql/data
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U cal"]
        interval: 5s
        timeout: 5s
        retries: 5
  volumes:
    pgdata:
  ```

### 2.3 — Configuration & Testing

- [x] Ensure all config comes from environment variables
- [x] Run migrations on container startup (or via entrypoint script)
- [x] Test full stack: `docker compose up --build`
- [x] Verify app accessible at `http://localhost:8501`

---

## ☸️ Milestone 3: Kubernetes Deployment

**Goal:** Production-ready deployment on Kubernetes.

### 3.1 — Kubernetes Manifests

- [x] Create `k8s/` directory with:
  - `namespace.yaml` — dedicated namespace
  - `deployment.yaml` — Streamlit app deployment
  - `service.yaml` — ClusterIP or LoadBalancer service
  - `configmap.yaml` — non-sensitive configuration
  - `secret.yaml` — database credentials (external DB URL)
  - `ingress.yaml` — external access (optional, depends on setup)

### 3.2 — PostgreSQL on Kubernetes

- [ ] Option A: **StatefulSet** — run PostgreSQL in K8s with persistent volume
- [ ] Option B: **Managed database** — use Cloud SQL (GCP) or RDS (AWS) for production reliability
- [x] Option C: **External database** — use existing PostgreSQL (Cloud SQL, RDS, self-hosted, etc.); provide `DATABASE_URL` and credentials via K8s Secret; no DB in cluster

---

## 🔮 Milestone 4: Future Enhancements

These are planned features to be implemented after the core app is stable.

### 4.1 — Google Sheets Integration
- [ ] Import game catalog from Google Sheets via `gspread`
- [ ] Service Account setup & credentials management
- [ ] Manual sync trigger from admin page
- [ ] Auto-sync on app startup (optional)

### 4.2 — Migrate to Flask (Optional)
> If Streamlit becomes too constraining for the UI, consider migrating to Flask.

- [ ] Flask + Jinja2 templates with Bootstrap/Tailwind CSS
- [ ] Proper URL routing (`/vote`, `/admin`, `/results`)
- [ ] Better mobile-first responsive design
- [ ] User session management

### 4.3 — Google OAuth Login ✅
- [x] **Streamlit native auth** — use `st.login()` / `st.logout()` (Streamlit 1.42+)
- [x] Add `Authlib>=1.3.2` to requirements
- [x] Configure `.streamlit/secrets.toml` or env vars
- [x] **Google Cloud setup** — create OAuth 2.0 Web client, consent screen, redirect URI
- [x] Replace "Your Name" text input on Vote page with login gate when OAuth configured
- [x] **DB migration** — add `google_id`, `email` to `User`; drop unique on `name`
- [x] **My Votes** section — expandable view of current user's votes, easy edit flow
- [x] **Fallback** — legacy name-based voting when OAuth not configured

### 4.4 — Event History
- [ ] Support multiple game night events
- [ ] Archive past events with their assignments
- [ ] View history of past game nights

### 4.5 — Notifications
- [ ] Email or Slack notifications when voting opens/closes
- [ ] Notify unassigned users to pick a table

---

## 🚦 Current Status

| Milestone | Status |
|-----------|--------|
| 1. Local Python App | ✅ Done |
| 2. Dockerize | ✅ Done |
| 3. Kubernetes | ✅ Done |
| 4. Enhancements | ⏳ Waiting |

---

## 🛠 Tech Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | **Streamlit** (start here) | Fastest to prototype, pure Python, good enough for 8-12 users. Can migrate to Flask later if needed. |
| Database | **PostgreSQL** | Production-grade, works the same locally and in K8s. |
| Local DB | **Docker Compose** | No need to install PostgreSQL natively. One command to start. |
| ORM | **SQLAlchemy** | Industry standard Python ORM, works great with Alembic migrations. |
| Migrations | **Alembic** | Reliable schema versioning, auto-generates migration scripts. |
| Containerization | **Docker** | Standard, works everywhere. |
| Orchestration | **Kubernetes** | Scalable, production-ready, matches your deployment target. |
| IaC | **Terraform** | Already available on your machine, great for GKE/cloud infra. |
