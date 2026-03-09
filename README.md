# 🎲 Board Game Night Planner

A web application for organizing board game nights with a group of 8–12 players. Users submit their top three game preferences, the system identifies the most popular titles, and automatically assigns players to physical tables — with a manual fallback for anyone who can't be placed.

**Implemented:** Vote, Add Game, Current Games (view/edit/delete), Results, Admin (Import XLSX, algorithms, physical tables), Help, light/dark theme, **Google OAuth login** (store votes by account, easy access & edit). Entry redirects to Vote. **Planned:** Google Sheets import.

---

## 📋 Table of Contents

- [Full Flow: How to Use](#-full-flow-how-to-use)
- [Screenshots](#-screenshots)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [How It Works](#-how-it-works)
  - [Phase 1: Scoring & Game Selection](#phase-1-scoring--game-selection)
  - [Phase 2: Player Assignment](#phase-2-player-assignment)
  - [Phase 3: Fallback for Unassigned Players](#phase-3-fallback-for-unassigned-players)
- [Pages Overview](#-pages-overview)
- [Admin Features](#-admin-features)
- [Database Schema (PostgreSQL)](#-database-schema-postgresql)
- [Getting Started](#-getting-started)

---

## ✅ What's Implemented

| Feature | Status |
|---------|--------|
| Weighted voting (top 3 games) | ✅ |
| Add game manually | ✅ |
| Import games from XLSX (Admin) | ✅ |
| Current Games page (view/edit/delete) | ✅ |
| Physical tables (name, capacity) | ✅ |
| Calculate Scores & Select Games | ✅ |
| Run Player Assignment (first-come, first-served) | ✅ |
| Manual table pick for unassigned players | ✅ |
| Vote as entry page (Home redirects) | ✅ |
| Light/dark theme toggle | ✅ |
| Docker & Kubernetes deployment | ✅ |
| Google OAuth login | ✅ |

---

## ✅ What's Implemented

| Feature | Status |
|---------|--------|
| Weighted voting (top 3 games) | ✅ |
| XLSX import (BGG, Kocie-gierce format) | ✅ |
| Physical tables (configurable seats) | ✅ |
| Calculate scores & select games | ✅ |
| Automatic player assignment (first-come, first-served) | ✅ |
| Manual fallback for unassigned players | ✅ |
| Home → Vote redirect (entry page) | ✅ |
| Light/dark theme toggle | ✅ |
| Google OAuth login | ✅ |

---

## 📸 Screenshots

### 🗳️ Vote Page
![Vote](screenshoot1.png)

### 📊 Results Page
![Results](screenshoot2.png)

### ⚙️ Admin Dashboard
![Admin](screenshoot3.png)

---

## 🛠 Tech Stack

| Component   | Technology                          |
| ----------- | ----------------------------------- |
| Language    | Python                              |
| Framework   | Streamlit (or Flask as alternative) |
| Database    | PostgreSQL                          |

---

## ✨ Features

- **Weighted voting** — users pick their top 3 games, ranked by preference
- **Automatic table assignment** — first-come, first-served based on submission time
- **Multiple tables per game** — popular games can run on 2+ tables simultaneously
- **Configurable player limits** — set min/max players per game
- **Fallback mechanism** — unassigned players manually pick from tables with open seats
- **XLSX import** — bulk import games from xlsx (BGG format, multi-sheet)
- **Physical tables** — define real tables (e.g. 2×6, 2×4 seats) and assign games
- **Theme toggle** — light/dark mode
- **Google OAuth login** — sign in with Google to store votes by account; view and edit your votes easily

---

## 📖 Full Flow: How to Use

1. **Entry** — Opening the app redirects you to the **Vote** page.
2. **Vote** — Log in with Google (or enter your name if OAuth isn't configured), pick your top 3 games (1st, 2nd, 3rd choice), and submit. Your votes are stored with your account. Change and resubmit anytime to update.
3. **Add games** — Admins add games manually (**➕ Add Game**) or import from XLSX (**⚙️ Admin**).
4. **View catalog** — **📋 Current Games** shows all games and lets you edit or delete them.
5. **Run algorithms** — In **⚙️ Admin**, click **Calculate Scores & Select Games** to pick which games will run based on votes, then **Run Player Assignment** to assign players to tables.
6. **Physical tables** — Admins define tables (e.g. 2×6 seats, 2×4 seats) and assign selected games to each table.
7. **Results** — **📊 Results** shows table assignments. Unassigned players can manually pick a table with open seats.

---

## ⚙ How It Works (Algorithms)

### Phase 1: Scoring & Game Selection

Each user submits their top 3 game choices. Votes are weighted:

| Rank       | Points |
| ---------- | ------ |
| 1st choice | 3      |
| 2nd choice | 2      |
| 3rd choice | 1      |

The total score for a game is calculated as:

```
Score = 3 × (# of 1st-choice votes) + 2 × (# of 2nd-choice votes) + 1 × (# of 3rd-choice votes)
```

Games that meet a minimum point threshold **and** have enough interested players to satisfy their `min_players` requirement are selected. The system creates **physical table** assignments (each physical table gets one selected game).

### Phase 2: Player Assignment

Players are assigned to tables using a **first-come, first-served** approach based on the exact timestamp of their form submission:

1. Users are sorted chronologically by submission time
2. The system tries to seat each user at the table of their **1st choice**
3. If that table is full (or the game wasn't selected), it tries the **2nd choice**, then the **3rd**
4. If multiple tables exist for the same game, the system fills them in order

> 💡 **Why first-come, first-served?** It's simple, transparent, and rewards users who submit early — no complex tie-breaking needed.

### Phase 3: Fallback for Unassigned Players

If a user can't be placed at any of their three choices, they are flagged as **unassigned**. When they open the app, they see a special view showing only the tables that still have open seats, and they manually pick one.

---

## 📄 Pages & Admin Features

| Page              | Description                                                                 |
| ----------------- | --------------------------------------------------------------------------- |
| **🗳️ Vote**       | Entry page. Submit your name and top 3 game choices.                         |
| **➕ Add Game**   | Add a new game manually (title, min/max players).                             |
| **📋 Current Games** | View all games in a table; edit or delete games.                         |
| **📊 Results**    | View game scores, table assignments, and who has voted. Unassigned players pick a table manually. |
| **⚙️ Admin**      | Import from XLSX, run algorithms (Calculate Scores, Player Assignment, Reset), manage physical tables, assign games to tables, overview metrics. |
| **❓ Help**       | How the app works.                                                          |
| **👤 User Settings** | Change your display name (OAuth only).                                      |

| Admin Feature           | Description                                                                 |
| ----------------------- | --------------------------------------------------------------------------- |
| **Import from XLSX**    | Upload xlsx (BGG ID, name, player count). Supports multi-sheet, Kocie-gierce format. |
| **Physical tables**     | Add/edit tables (name, capacity). Assign selected games to each table.       |
| **Calculate Scores**   | Select games by weighted votes; auto-assign them to physical tables.        |
| **Run Player Assignment** | Assign players to tables (first-come, first-served by submission time). |
| **Reset Assignments**   | Clear all player-to-table assignments.                                     |

---

## 🗄 Database Schema (PostgreSQL)

### `users`

| Column              | Type                       | Description                                |
| ------------------- | -------------------------- | ------------------------------------------ |
| `id`                | `SERIAL PRIMARY KEY`       | Unique user ID                             |
| `name`              | `VARCHAR(255) NOT NULL`    | User's display name                        |
| `google_id`         | `VARCHAR(255) UNIQUE`      | OAuth subject ID (nullable for legacy)     |
| `email`             | `VARCHAR(255)`             | User email from OAuth                       |
| `submitted_at`      | `TIMESTAMP`                | When the user submitted preferences        |
| `assigned_table_id` | `INTEGER REFERENCES table_instances(id)` | Which table the user is assigned to |

### `games`

| Column         | Type                    | Description                              |
| -------------- | ----------------------- | ---------------------------------------- |
| `id`           | `SERIAL PRIMARY KEY`    | Unique game ID                           |
| `bgg_id`       | `INTEGER` (nullable)    | BoardGameGeek ID (optional)              |
| `bgg_id`       | `INTEGER`               | BoardGameGeek ID (optional)              |
| `title`        | `VARCHAR(255) NOT NULL` | Name of the board game                   |
| `min_players`  | `INTEGER NOT NULL`      | Minimum players required                 |
| `max_players`  | `INTEGER NOT NULL`      | Maximum players allowed                  |
| `is_selected`  | `BOOLEAN DEFAULT FALSE` | Whether the game qualified for play      |

### `tables` (physical tables)

| Column       | Type                    | Description                    |
| ------------ | ----------------------- | ------------------------------ |
| `id`         | `SERIAL PRIMARY KEY`    | Unique table ID                |
| `name`       | `VARCHAR(100) NOT NULL`  | Table name (e.g. "Table 1")    |
| `capacity`   | `INTEGER NOT NULL`      | Seats (e.g. 4 or 6)            |
| `sort_order` | `INTEGER NOT NULL`      | Display order                  |

### `table_instances`

| Column    | Type                                  | Description                          |
| --------- | ------------------------------------- | ------------------------------------ |
| `id`      | `SERIAL PRIMARY KEY`                  | Unique table instance ID             |
| `table_id`| `INTEGER REFERENCES tables(id)`       | Physical table                       |
| `game_id` | `INTEGER REFERENCES games(id)`         | Which game is played at this table   |

> Each physical table has at most one game. A game can run on multiple physical tables (e.g. 2 Catan tables).

### `preferences`

| Column    | Type                                | Description                        |
| --------- | ----------------------------------- | ---------------------------------- |
| `id`      | `SERIAL PRIMARY KEY`                | Unique preference ID               |
| `user_id` | `INTEGER REFERENCES users(id)`      | Who submitted this preference      |
| `game_id` | `INTEGER REFERENCES games(id)`      | Which game was chosen               |
| `rank`    | `INTEGER CHECK (rank IN (1, 2, 3))` | Preference rank (1st, 2nd, or 3rd) |

### Entity Relationships

```
users ──────────── preferences ──────────── games
  │                                           │
  │  assigned to                  has many    │
  ▼                                           ▼
table_instances ◄──────────────────────────────┘
       │
       │ links to
       ▼
    tables (physical)
```

---

## 📊 Google Sheets Integration (Planned)

> **Status:** 🔜 Planned feature

Import your game catalog directly from a Google Sheet instead of manually adding games to the database.

**How it will work:**

1. Maintain a Google Sheet with columns: `Title`, `Min Players`, `Max Players`
2. The app connects via `gspread` + Google Service Account credentials
3. On sync (manual trigger or at startup), games are upserted into the `games` table
4. New games appear in voting options; removed games are handled gracefully

**Required setup (when implemented):**
- Google Cloud project with Sheets API enabled
- Service Account with read access to the spreadsheet
- Credentials JSON file configured in the app

---

> 📌 See [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) for the full development roadmap.

---

## 🚀 Getting Started

### Option 1: Docker (recommended)

```bash
git clone <repo-url>
cd cal

docker compose up --build
```

Then open http://localhost:8501. The app runs migrations on startup.

### Option 2: Local Python

```bash
git clone <repo-url>
cd cal

# Start PostgreSQL (Docker)
docker compose up -d db

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and adjust if needed
cp .env.example .env

# Run migrations
alembic upgrade head

# Run the app (Home redirects to Vote)
streamlit run Home.py
```

### Google OAuth (optional)

To enable "Log in with Google" for storing votes by account:

#### 1. Google Cloud Console setup

Go to [Google Auth Platform](https://console.cloud.google.com/auth/overview) and select your project.

**a) OAuth consent screen (first-time only)**

- Left menu → **OAuth consent screen**
- User type: **External** (for anyone with a Google account) or **Internal** (for your org only)
- Click **Create**

  *App information:*
  - App name: e.g. `Board Game Night Planner`
  - User support email: your email
  - Developer contact: your email

  *Scopes:*
  - Click **Add or remove scopes**
  - Add `openid`, `.../auth/userinfo.email`, and `.../auth/userinfo.profile` (minimal for sign-in)
  - Save

  *Test users (if app is in "Testing"):*
  - Under **Test users**, click **Add users**
  - Add the Google accounts that will log in (e.g. your own). Only these accounts can log in until the app is verified/published.
  - Until verified, apps in Testing mode are limited to 100 logins with sensitive scopes.

**b) Create OAuth client (if you haven’t already)**

- Left menu → **Credentials** (or **Clients**)
- **Create Credentials** → **OAuth client ID**
- Application type: **Web application**
- Name: e.g. `Board Game Night`

- Under **Authorized redirect URIs**, click **Add URI** and add:
  - Local: `http://localhost:8501/oauth2callback`
  - Production (if applicable): `https://your-domain.com/oauth2callback`

- Click **Create**. Copy the **Client ID** and **Client secret** and store them securely — the secret is only shown once.

#### 2. Configure the app

Copy the example secrets file and edit it:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "paste_a_long_random_string_here"   # e.g. run: openssl rand -hex 32
client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

- `client_id` / `client_secret`: from the Google Cloud Console
- `cookie_secret`: generate with `openssl rand -hex 32`
- `redirect_uri`: must exactly match one of the URIs in the Google Console (including port and path)

> **Security:** Never commit `.streamlit/secrets.toml` to version control — it is listed in `.gitignore`.

#### 3. Restart the app

After saving `secrets.toml`, restart the app. The Vote page will show **Log in with Google**. Without OAuth config, the app falls back to name-based voting.

#### Troubleshooting

| Error | Fix |
|-------|-----|
| "redirect_uri_mismatch" | Make sure the URI in `secrets.toml` exactly matches one in Google Console → Credentials → Your OAuth client → Authorized redirect URIs |
| "Access blocked: This app's request is invalid" | Add your Google account as a Test user in OAuth consent screen → Test users |
| "100 sensitive scope logins" limit | Use Test users in Testing mode, or complete app verification for production use |

### Build & Push (for Kubernetes / registry)

```bash
# Build the image
docker build -t your-registry/cal:latest .

# Push to your registry (login first if needed: docker login)
docker push your-registry/cal:latest
```

Replace `your-registry` with your registry (e.g. `ghcr.io/your-org`, `gcr.io/your-project`, `docker.io/your-user`).

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
