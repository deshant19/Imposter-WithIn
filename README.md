# 🕵️ Imposter Within

> A real-time multiplayer social deduction party game for 3–20 players.  
> Built with **React 18** on the frontend and **Python / FastAPI** on the backend,  
> communicating over **WebSockets** with **JSON file** persistence.

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Tech Stack](#2-tech-stack)
3. [Game Rules](#3-game-rules)
4. [Prerequisites](#4-prerequisites)
5. [Installation & Running](#5-installation--running)
6. [Environment Variables](#6-environment-variables)
7. [API Reference](#7-api-reference)
8. [WebSocket Events](#8-websocket-events)
9. [Running the Test Suite](#9-running-the-test-suite)
10. [Test Suite Overview](#10-test-suite-overview)
11. [Docker Environment](#11-docker-environment)
12. [Database — JSON File Storage](#12-database--json-file-storage)
13. [Architecture Overview](#13-architecture-overview)
14. [Imposter Count Rules](#14-imposter-count-rules)
15. [CI / CD Integration](#15-ci--cd-integration)
16. [Contributing](#16-contributing)

---

## 1. Project Structure

```
ImposterWithIn/
│
├── README.md                          ← You are here
├── run_tests.sh                       ← One-command test runner (all suites)
├── docker-compose.test.yml            ← Docker environment for running tests
│
├── backend/                           ← Python FastAPI application
│   ├── main.py                        ← Application entry point (all routes + WS)
│   ├── requirements.txt               ← Runtime Python dependencies
│   ├── requirements-test.txt          ← Test-only Python dependencies
│   ├── pytest.ini                     ← pytest configuration + coverage thresholds
│   ├── Dockerfile.test                ← Docker image for backend test execution
│   │
│   ├── data/
│   │   └── rooms.json                 ← Live database (auto-created, git-ignored in prod)
│   │
│   └── tests/                         ← Complete backend test suite (134 tests)
│       ├── __init__.py
│       ├── conftest.py                ← Shared fixtures: isolated storage, AsyncClient, factories
│       ├── test_game_logic.py         ← Pure unit tests: imposter count, role assignment, file I/O
│       ├── test_rooms_create.py       ← POST /rooms + GET /health integration tests
│       ├── test_rooms_join_leave.py   ← Join, get room, leave room integration tests
│       ├── test_game_flow.py          ← Start game, reset game integration tests
│       ├── test_websocket.py          ← WebSocket connection + real-time notification tests
│       └── test_edge_cases.py         ← Concurrency, boundary values, chaos / corrupt-state tests
│
└── frontend/                          ← React 18 single-page application
    ├── package.json                   ← npm dependencies + test scripts
    ├── babel.config.js                ← Babel config for Jest JSX transform
    ├── jest.config.js                 ← Jest configuration + coverage thresholds
    ├── Dockerfile.test                ← Docker image for frontend test execution
    │
    ├── public/
    │   └── index.html                 ← HTML shell (loads Google Fonts, mounts #root)
    │
    └── src/
        ├── index.js                   ← ReactDOM.createRoot entry point
        ├── App.jsx                    ← Complete application (all screens + components)
        │
        └── __tests__/                 ← Complete frontend test suite (55 tests)
            ├── setup.js               ← Global mocks: fetch, WebSocket, clipboard
            ├── App.test.jsx           ← Component integration tests (all 4 screens)
            └── __mocks__/
                ├── styleMock.js       ← Stub for CSS imports in Jest
                └── fileMock.js        ← Stub for image/asset imports in Jest
```

---

## 2. Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | React | 18.2 | UI framework |
| **Frontend** | React DOM | 18.2 | DOM rendering |
| **Frontend Styles** | Pure CSS (injected) | — | Animations, layout, theming |
| **Frontend Fonts** | Google Fonts (Syne + Space Mono) | — | Typography |
| **Backend** | Python | 3.11+ | Runtime |
| **Backend** | FastAPI | 0.111 | REST API + WebSocket server |
| **Backend** | Uvicorn | 0.30 | ASGI server |
| **Backend** | Pydantic | v2 | Request/response validation |
| **Realtime** | WebSockets | native | Browser ↔ server push events |
| **Database** | JSON files | — | `backend/data/rooms.json` |
| **Backend Tests** | pytest + pytest-asyncio | 8.2 | Test runner |
| **Backend Tests** | httpx | 0.27 | Async HTTP test client |
| **Backend Tests** | pytest-cov | 5.0 | Coverage reports |
| **Frontend Tests** | Jest | 29 | Test runner |
| **Frontend Tests** | React Testing Library | 14 | Component testing |
| **Frontend Tests** | @testing-library/user-event | 14 | User interaction simulation |
| **Containerisation** | Docker + Docker Compose | — | Test environment |

---

## 3. Game Rules

1. **3 to 20 players** can join a single room.
2. The **host** creates a room and shares a **6-letter code** with other players.
3. Every player enters their **name** before entering the room.
4. When the host starts the game, each player privately sees their role:

| Card | Background | Text | Meaning |
|------|-----------|------|---------|
| Secret word (e.g. *telescope*) | 🟩 Green | White | You are an **Agent** — discuss the word without saying it outright |
| `IMPOSTER` | 🟥 Red | White | You are an **Imposter** — bluff your way through without knowing the word |

5. Players **discuss** freely — agents try to expose imposters; imposters try to blend in.
6. Players **vote** (verbally or via a separate mechanism) to eliminate who they think is an imposter.
7. **Agents win** by correctly exposing all imposters. **Imposters win** by surviving.
8. The host can **reset** at any time to start a new round with the same players.

---

## 4. Prerequisites

| Tool | Minimum Version | Check |
|------|----------------|-------|
| Python | 3.11 | `python3 --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| Docker *(optional, for tests)* | 24 | `docker --version` |

---

## 5. Installation & Running

### Backend

```bash
# 1. Enter the backend directory
cd ImposterWithIn/backend

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows

# 3. Install runtime dependencies
pip install -r requirements.txt

# 4. Seed the database file
mkdir -p data && echo '{}' > data/rooms.json

# 5. Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend is now running at **http://localhost:8000**  
Interactive API docs available at **http://localhost:8000/docs**

---

### Frontend

```bash
# 1. Enter the frontend directory
cd ImposterWithIn/frontend

# 2. Install dependencies
npm install

# 3. Start the development server
npm start
```

Frontend is now running at **http://localhost:3000**

> The `"proxy": "http://localhost:8000"` setting in `package.json` proxies all
> `/rooms` and `/ws` requests to the backend during development.

---

### Playing Locally (Multi-tab / Multi-device)

| Scenario | How |
|----------|-----|
| Multiple players, one machine | Open `http://localhost:3000` in separate browser tabs |
| Multiple players, local network | Replace `localhost` in `API` and `WS_BASE` constants in `App.jsx` with your machine's LAN IP (e.g. `192.168.1.42`) |

---

## 6. Environment Variables

The application uses hardcoded constants for simplicity. To change the backend URL, edit the top of `frontend/src/App.jsx`:

```js
const API     = "http://localhost:8000";   // ← REST base URL
const WS_BASE = "ws://localhost:8000";     // ← WebSocket base URL
```

For production deployments these should be injected via `.env`:

```
REACT_APP_API_URL=https://api.yourserver.com
REACT_APP_WS_URL=wss://api.yourserver.com
```

---

## 7. API Reference

All endpoints return JSON. Error responses follow the shape `{ "detail": "<message>" }`.

### Health Check

```
GET /health
```
```json
{ "status": "ok", "service": "Imposter Within" }
```

---

### Create Room

```
POST /rooms
Content-Type: application/json

{ "host_name": "Alice" }
```

**Response 200**
```json
{
  "room_code":   "ABCDEF",
  "player_id":   "p_1718000000000_4321",
  "player_name": "Alice"
}
```

| Error | Status | Reason |
|-------|--------|--------|
| Empty name | 400 | `"Name cannot be empty"` |
| Missing field | 422 | Pydantic validation |

---

### Join Room

```
POST /rooms/{code}/join
Content-Type: application/json

{ "player_name": "Bob" }
```

**Response 200**
```json
{
  "room_code":   "ABCDEF",
  "player_id":   "p_1718000000001_5678",
  "player_name": "Bob",
  "host_id":     "p_1718000000000_4321",
  "players": [
    { "id": "p_...4321", "name": "Alice" },
    { "id": "p_...5678", "name": "Bob" }
  ]
}
```

| Error | Status | Reason |
|-------|--------|--------|
| Room not found | 404 | Wrong code |
| Game already started | 400 | Status is `playing` |
| Room full | 400 | ≥ 20 players |
| Duplicate name | 400 | Case-insensitive match |
| Empty name | 400 | Validation |

---

### Get Room

```
GET /rooms/{code}
```

**Response 200**
```json
{
  "code":           "ABCDEF",
  "host_id":        "p_...4321",
  "players":        [ ... ],
  "status":         "waiting",
  "imposter_count": 0
}
```

---

### Start Game *(host only)*

```
POST /rooms/{code}/start?player_id=p_...4321
```

**Response 200**
```json
{ "status": "started", "imposter_count": 1 }
```

Each connected player also receives a private **WebSocket** message — see §8.

| Error | Status | Reason |
|-------|--------|--------|
| Not the host | 403 | Only host can start |
| < 3 players | 400 | Minimum not met |
| Already playing | 400 | Game in progress |
| Room not found | 404 | — |

---

### Reset Game *(host only)*

```
POST /rooms/{code}/reset?player_id=p_...4321
```

**Response 200**
```json
{ "status": "reset" }
```

All connected players also receive a **WebSocket** `game_reset` broadcast.

---

### Leave Room

```
DELETE /rooms/{code}/leave?player_id=p_...4321
```

**Response 200**
```json
{ "status": "left" }
```

If the last player leaves:
```json
{ "status": "room_deleted" }
```

---

### WebSocket Connection

```
WS /ws/{code}/{player_id}
```

Connect once after joining or creating a room. Send `"ping"` every 25 s to keep the connection alive; the server responds with `"pong"`.

---

## 8. WebSocket Events

All events are JSON objects with a `type` field.

### Server → Client

#### `connected`
Sent immediately after the WebSocket handshake completes.
```json
{ "type": "connected", "player_id": "p_...4321" }
```

#### `player_joined`
Broadcast to all players already in the room when someone new joins.
```json
{
  "type":        "player_joined",
  "player_name": "Carol",
  "players":     [ ... ],
  "message":     "🎮 Carol joined the room!"
}
```

#### `game_started`
Sent **individually** to each player when the host starts the game.  
Every player gets a different `assignment`.
```json
{
  "type":          "game_started",
  "assignment":    "telescope",
  "is_imposter":   false,
  "total_players": 5,
  "imposter_count": 2
}
```

#### `game_reset`
Broadcast to all players when the host resets the round.
```json
{
  "type":    "game_reset",
  "players": [ ... ],
  "message": "🔄 Host reset the game. Back to the lobby!"
}
```

#### `player_left`
Broadcast when a player disconnects via the Leave button.
```json
{
  "type":        "player_left",
  "player_name": "Bob",
  "players":     [ ... ],
  "new_host_id": "p_...5678",
  "message":     "👋 Bob left the room."
}
```

### Client → Server

| Message | Response | Purpose |
|---------|----------|---------|
| `"ping"` | `"pong"` | Keepalive |

---

## 9. Running the Test Suite

### Option A — Shell Script (recommended for local dev)

```bash
cd ImposterWithIn

# All tests (backend + frontend)
./run_tests.sh

# Backend only
./run_tests.sh --backend

# Frontend only
./run_tests.sh --frontend

# Only fast pure-unit tests (no HTTP, no WebSocket)
./run_tests.sh --unit

# Full run + HTML coverage reports
./run_tests.sh --coverage

# CI mode (fail-fast, no watch prompts)
./run_tests.sh --ci

# Frontend in interactive watch mode
./run_tests.sh --watch
```

The script automatically creates the Python venv and installs all dependencies on first run.

---

### Option B — Docker (zero local setup)

```bash
cd ImposterWithIn

# Run both suites in isolated containers
docker compose -f docker-compose.test.yml up --build

# Backend only
docker compose -f docker-compose.test.yml up --build backend

# Frontend only
docker compose -f docker-compose.test.yml up --build frontend
```

HTML coverage reports are written to:
```
ImposterWithIn/test-reports/backend/coverage_html/index.html
ImposterWithIn/test-reports/frontend/lcov-report/index.html
```

---

### Option C — Manual

#### Backend

```bash
cd ImposterWithIn/backend
source venv/bin/activate
pip install -r requirements-test.txt

# All tests
pytest tests/ -v

# Single file
pytest tests/test_game_logic.py -v

# Single test
pytest tests/test_game_logic.py::TestGetImposterCount::test_three_to_four_players_one_imposter -v

# With coverage
pytest tests/ --cov=main --cov-report=html:coverage_html
```

#### Frontend

```bash
cd ImposterWithIn/frontend
npm install

# Interactive (re-runs on change)
npm test

# One-shot CI run
npm run test:ci

# With coverage
npm run test:coverage
```

---

## 10. Test Suite Overview

### Backend — 134 Tests across 6 files

| File | Tests | Layer |
|------|------:|-------|
| `test_game_logic.py` | 32 | Pure unit — no HTTP, no file I/O mocking |
| `test_rooms_create.py` | 16 | Integration — `POST /rooms`, `GET /health` |
| `test_rooms_join_leave.py` | 22 | Integration — join, get room, leave |
| `test_game_flow.py` | 28 | Integration — start game, reset game |
| `test_websocket.py` | 18 | WebSocket — connection, ping, all 5 event types |
| `test_edge_cases.py` | 18 | Concurrency, corpus, boundary values, chaos |

**Coverage target:** ≥ 80% lines on `main.py`

Key design decisions:
- Every test runs with its **own isolated `rooms.json`** via `tmp_path` monkeypatching — no test ever touches the real database.
- The `conftest.py` `isolated_storage` fixture runs **automatically** for every test (`autouse=True`).
- WebSocket tests use FastAPI's built-in `TestClient` (synchronous) which correctly handles ASGI WebSocket upgrade.
- Async REST tests use `httpx.AsyncClient` with `ASGITransport` — no real network calls.

---

### Frontend — 55 Tests in 1 file

| Describe Block | Tests | What is covered |
|----------------|------:|-----------------|
| Landing Screen | 6 | Title, buttons, navigation |
| Entry Screen — Create | 8 | Name input, validation, API success/error |
| Entry Screen — Join | 7 | Code input, uppercase enforcement, validation |
| Lobby Screen | 7 | Room code display, player list, WS events |
| Game Screen | 10 | Pre-reveal gate, role cards, reset flow |
| Avatar Colour Helper | 2 | Deterministic colour mapping |
| Accessibility | 2 | Button labels, input presence |

**Coverage target:** ≥ 70% lines, ≥ 60% branches

Key design decisions:
- `global.fetch` is replaced with `jest.fn()` — every test controls API responses via `mockResolvedValueOnce`.
- `global.WebSocket` is replaced with a `MockWebSocket` class that exposes a `simulateMessage()` helper, letting tests trigger server-push events.
- `ReactDOM.createRoot` is mocked so the app module can be imported without auto-mounting.

---

## 11. Docker Environment

### `docker-compose.test.yml`

```
┌─────────────────────┐    ┌─────────────────────┐
│  iw_backend_tests   │    │  iw_frontend_tests   │
│  python:3.12-slim   │    │  node:20-slim        │
│                     │    │                      │
│  pytest + coverage  │    │  jest (CI mode)      │
│         ↓           │    │         ↓            │
│  /reports → host    │    │  /coverage → host    │
└─────────────────────┘    └─────────────────────┘
           ↓                          ↓
      test-reports/              test-reports/
      backend/                   frontend/
      coverage_html/             lcov-report/
```

Both services run in parallel. A lightweight `reporter` container prints the summary after both finish.

### `backend/Dockerfile.test`

```
FROM python:3.12-slim
COPY requirements-test.txt main.py tests/ pytest.ini → /app
RUN pip install -r requirements-test.txt
CMD pytest tests/ -v --cov=main --cov-report=html:/reports/...
```

### `frontend/Dockerfile.test`

```
FROM node:20-slim
COPY package.json → /app && npm install
COPY src/ public/ babel.config.js jest.config.js → /app
CMD npm run test:ci
```

---

## 12. Database — JSON File Storage

All game state is stored in a single file: `backend/data/rooms.json`.

### Schema

```json
{
  "ABCDEF": {
    "code":           "ABCDEF",
    "host_id":        "p_1718000000000_4321",
    "players": [
      { "id": "p_1718000000000_4321", "name": "Alice" },
      { "id": "p_1718000000001_5678", "name": "Bob"   }
    ],
    "status":         "waiting",
    "assignments": {
      "p_1718000000000_4321": "telescope",
      "p_1718000000001_5678": "IMPOSTER"
    },
    "word":           "telescope",
    "imposter_count": 1,
    "created_at":     1718000000.0
  }
}
```

### Lifecycle

```
POST /rooms        → room created,  status = "waiting"
POST /join         → player appended to players[]
POST /start        → assignments filled, status = "playing"
POST /reset        → assignments cleared, status = "waiting"
DELETE /leave      → player removed; room deleted if empty
```

### Fault Tolerance

- `load_rooms()` catches both `json.JSONDecodeError` and `IOError`, returning `{}` on any failure.
- `save_rooms()` always writes the complete state (last-write-wins).
- Missing optional keys (e.g. `imposter_count` in legacy rooms) are handled with `.get()` defaults.

---

## 13. Architecture Overview

```
 Browser (Player 1)              Browser (Player 2)
 ┌──────────────────┐            ┌──────────────────┐
 │  React 18 SPA    │            │  React 18 SPA    │
 │  App.jsx         │            │  App.jsx         │
 │  ┌────────────┐  │            │  ┌────────────┐  │
 │  │ REST fetch │◄─┼────────────┼─►│ REST fetch │  │
 │  │ WebSocket  │◄─┼──────┐   ┌┼─►│ WebSocket  │  │
 │  └────────────┘  │      │   │└──────────────────┘
 └──────────────────┘      │   │
                            ▼   ▼
              ┌─────────────────────────────┐
              │     FastAPI (uvicorn)        │
              │                             │
              │  REST routes (7 endpoints)  │
              │  WebSocket /ws/{code}/{id}  │
              │                             │
              │  connections{}              │ ← in-memory WS registry
              │        ↓                   │
              │  load_rooms() / save_rooms()│
              │        ↓                   │
              │  backend/data/rooms.json   │ ← persistent storage
              └─────────────────────────────┘
```

### Key Design Choices

| Decision | Rationale |
|----------|-----------|
| Single `App.jsx` | Avoids build complexity for a game prototype; all screens as inner functions |
| JSON file DB | Simple, human-readable, no external dependencies, survives server restart |
| WebSockets for notifications | Instant push (no polling) — critical for "player joined" UX |
| In-memory WS registry | Fast O(1) lookup; connections are ephemeral and don't need persistence |
| `autouse` test fixture | Guarantees every test gets a clean database regardless of execution order |

---

## 14. Imposter Count Rules

| Players | Imposters | Agents |
|---------|----------:|-------:|
| 3 | 1 | 2 |
| 4 | 1 | 3 |
| 5 | 2 | 3 |
| 6 | 2 | 4 |
| 7 | 2 | 5 |
| 8 | 2 | 6 |
| 9 | 2 | 7 |
| 10 | 3 | 7 |
| 11–14 | 3 | 8–11 |
| 15 | 4 | 11 |
| 16–19 | 4 | 12–15 |

**Formula:**
```python
def get_imposter_count(n: int) -> int:
    if n < 5:
        return 1
    return 2 + (n - 5) // 5
```

**Invariant:** Imposters are always a strict minority (`imposters < agents`) for every valid player count (3–19).

---

## 15. CI / CD Integration

Add `.github/workflows/tests.yml` to your repository:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  backend-tests:
    name: Backend Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --tb=short --cov=main --cov-fail-under=80
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  frontend-tests:
    name: Frontend Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run tests
        run: cd frontend && npm run test:ci

  docker-tests:
    name: Docker Test Environment
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run all tests via Docker Compose
        run: docker compose -f docker-compose.test.yml up --build --exit-code-from backend
```

---

## 16. Contributing

```bash
# 1. Clone
git clone https://github.com/your-org/imposter-within.git
cd imposter-within

# 2. Create a feature branch
git checkout -b feat/my-feature

# 3. Make changes

# 4. Run the full test suite before committing
./run_tests.sh --ci

# 5. Push and open a Pull Request
```

### Adding a New Endpoint

1. Add the route to `backend/main.py`
2. Add at minimum: one happy-path test and one error-path test in the appropriate `tests/test_*.py` file
3. Run `pytest tests/ --cov=main` and verify coverage stays ≥ 80%

### Adding a New Frontend Screen

1. Add the component to `frontend/src/App.jsx`
2. Add at minimum: one render test and one interaction test in `src/__tests__/App.test.jsx`
3. Mock any new `fetch` calls in the test using `mockFetchSuccess()` / `mockFetchError()`

---

## License

MIT © Imposter Within Contributors
