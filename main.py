"""
Imposter Within — Backend
FastAPI + WebSockets + JSON file storage
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import random
import string
import asyncio
import time
from typing import Dict, Optional

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────

app = FastAPI(title="Imposter Within", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# File Paths
# ─────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ROOMS_FILE = os.path.join(DATA_DIR, "rooms.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# Word List (Common English Objects)
# ─────────────────────────────────────────────

WORD_LIST = [
    "telescope", "umbrella", "submarine", "lantern", "typewriter",
    "compass", "accordion", "briefcase", "chandelier", "escalator",
    "microscope", "calculator", "parachute", "saxophone", "periscope",
    "thermometer", "binoculars", "helicopter", "pendulum", "stapler",
    "magnifying glass", "harmonica", "abacus", "barometer", "metronome",
    "kaleidoscope", "boomerang", "catapult", "hourglass", "sextant",
    "gramophone", "percolator", "candelabra", "trebuchet", "zeppelin",
    "jackhammer", "turntable", "megaphone", "periscope", "altimeter",
    "stopwatch", "protractor", "xylophone", "wheelbarrow", "kettledrum",
    "lighthouse", "pinwheel", "slingshot", "sundial", "crowbar",
]

# ─────────────────────────────────────────────
# In-Memory WebSocket Registry
# ─────────────────────────────────────────────

# connections[room_code][player_id] = WebSocket
connections: Dict[str, Dict[str, WebSocket]] = {}


# ─────────────────────────────────────────────
# JSON File Helpers
# ─────────────────────────────────────────────

def load_rooms() -> dict:
    if not os.path.exists(ROOMS_FILE):
        return {}
    try:
        with open(ROOMS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_rooms(rooms: dict) -> None:
    with open(ROOMS_FILE, "w") as f:
        json.dump(rooms, f, indent=2)


def generate_room_code() -> str:
    """Generate a unique 6-letter uppercase room code."""
    return "".join(random.choices(string.ascii_uppercase, k=6))


# ─────────────────────────────────────────────
# Game Logic
# ─────────────────────────────────────────────

def get_imposter_count(n: int) -> int:
    """
    Rules:
      3–4  players → 1 imposter
      5–9  players → 2 imposters
      10–14 players → 3 imposters
      15–19 players → 4 imposters
      (every multiple of 5 starting from 5 adds 1 imposter)
    """
    if n < 5:
        return 1
    return 2 + (n - 5) // 5


def assign_roles(players: list) -> dict:
    """Return {player_id: 'IMPOSTER' | '<word>'} mapping."""
    n = len(players)
    imposter_count = get_imposter_count(n)
    player_ids = [p["id"] for p in players]
    imposters = set(random.sample(player_ids, imposter_count))
    word = random.choice(WORD_LIST)

    assignments = {}
    for pid in player_ids:
        assignments[pid] = "IMPOSTER" if pid in imposters else word
    return assignments, word, imposter_count


# ─────────────────────────────────────────────
# Broadcast Helper
# ─────────────────────────────────────────────

async def broadcast(room_code: str, payload: dict, exclude: Optional[str] = None):
    """Send a JSON message to all WebSocket clients in a room."""
    room_conns = connections.get(room_code, {})
    dead = []
    for pid, ws in room_conns.items():
        if pid == exclude:
            continue
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(pid)
    for pid in dead:
        room_conns.pop(pid, None)


async def send_to(room_code: str, player_id: str, payload: dict):
    """Send a JSON message to one specific player."""
    ws = connections.get(room_code, {}).get(player_id)
    if ws:
        try:
            await ws.send_json(payload)
        except Exception:
            pass


# ─────────────────────────────────────────────
# Request / Response Models
# ─────────────────────────────────────────────

class CreateRoomRequest(BaseModel):
    host_name: str


class JoinRoomRequest(BaseModel):
    player_name: str


# ─────────────────────────────────────────────
# REST Endpoints
# ─────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Imposter Within"}


@app.post("/rooms")
async def create_room(req: CreateRoomRequest):
    """Create a new room. Returns room code and host player ID."""
    if not req.host_name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    rooms = load_rooms()

    # Generate unique code
    code = generate_room_code()
    while code in rooms:
        code = generate_room_code()

    player_id = f"p_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    rooms[code] = {
        "code": code,
        "host_id": player_id,
        "players": [{"id": player_id, "name": req.host_name.strip()}],
        "status": "waiting",
        "assignments": {},
        "word": "",
        "imposter_count": 0,
        "created_at": time.time(),
    }
    save_rooms(rooms)

    return {
        "room_code": code,
        "player_id": player_id,
        "player_name": req.host_name.strip(),
    }


@app.post("/rooms/{code}/join")
async def join_room(code: str, req: JoinRoomRequest):
    """Join an existing room by code."""
    if not req.player_name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    rooms = load_rooms()

    if code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found. Check your code.")

    room = rooms[code]

    if room["status"] != "waiting":
        raise HTTPException(status_code=400, detail="Game has already started.")

    if len(room["players"]) >= 20:
        raise HTTPException(status_code=400, detail="Room is full (max 20 players).")

    # Check duplicate name
    existing_names = [p["name"].lower() for p in room["players"]]
    if req.player_name.strip().lower() in existing_names:
        raise HTTPException(status_code=400, detail="That name is already taken in this room.")

    player_id = f"p_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    player = {"id": player_id, "name": req.player_name.strip()}
    room["players"].append(player)
    save_rooms(rooms)

    # Notify all connected players
    await broadcast(code, {
        "type": "player_joined",
        "player_name": req.player_name.strip(),
        "players": room["players"],
        "message": f"🎮 {req.player_name.strip()} joined the room!",
    })

    return {
        "room_code": code,
        "player_id": player_id,
        "player_name": req.player_name.strip(),
        "players": room["players"],
        "host_id": room["host_id"],
    }


@app.get("/rooms/{code}")
async def get_room(code: str):
    """Get room state (players, status, host)."""
    rooms = load_rooms()
    if code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    room = rooms[code]
    return {
        "code": code,
        "host_id": room["host_id"],
        "players": room["players"],
        "status": room["status"],
        "imposter_count": room.get("imposter_count", 0),
    }


@app.post("/rooms/{code}/start")
async def start_game(code: str, player_id: str = Query(...)):
    """Start the game (host only). Assigns roles and notifies all players."""
    rooms = load_rooms()

    if code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")

    room = rooms[code]

    if room["host_id"] != player_id:
        raise HTTPException(status_code=403, detail="Only the host can start the game.")

    if len(room["players"]) < 3:
        raise HTTPException(status_code=400, detail="Need at least 3 players to start.")

    if room["status"] == "playing":
        raise HTTPException(status_code=400, detail="Game is already in progress.")

    assignments, word, imposter_count = assign_roles(room["players"])

    room["assignments"] = assignments
    room["status"] = "playing"
    room["word"] = word
    room["imposter_count"] = imposter_count
    save_rooms(rooms)

    # Send each player their individual assignment
    for player in room["players"]:
        pid = player["id"]
        assignment = assignments.get(pid, "")
        await send_to(code, pid, {
            "type": "game_started",
            "assignment": assignment,
            "is_imposter": assignment == "IMPOSTER",
            "total_players": len(room["players"]),
            "imposter_count": imposter_count,
        })

    return {"status": "started", "imposter_count": imposter_count}


@app.post("/rooms/{code}/reset")
async def reset_game(code: str, player_id: str = Query(...)):
    """Reset the game back to the lobby (host only)."""
    rooms = load_rooms()

    if code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")

    room = rooms[code]

    if room["host_id"] != player_id:
        raise HTTPException(status_code=403, detail="Only the host can reset the game.")

    room["status"] = "waiting"
    room["assignments"] = {}
    room["word"] = ""
    room["imposter_count"] = 0
    save_rooms(rooms)

    await broadcast(code, {
        "type": "game_reset",
        "players": room["players"],
        "message": "🔄 Host reset the game. Back to the lobby!",
    })

    return {"status": "reset"}


@app.delete("/rooms/{code}/leave")
async def leave_room(code: str, player_id: str = Query(...)):
    """Remove a player from the room."""
    rooms = load_rooms()

    if code not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")

    room = rooms[code]
    player_name = next((p["name"] for p in room["players"] if p["id"] == player_id), "Unknown")
    room["players"] = [p for p in room["players"] if p["id"] != player_id]

    # If room is empty, delete it
    if not room["players"]:
        del rooms[code]
        save_rooms(rooms)
        return {"status": "room_deleted"}

    # If host left, assign new host
    if room["host_id"] == player_id and room["players"]:
        room["host_id"] = room["players"][0]["id"]

    save_rooms(rooms)

    await broadcast(code, {
        "type": "player_left",
        "player_name": player_name,
        "players": room["players"],
        "new_host_id": room["host_id"],
        "message": f"👋 {player_name} left the room.",
    })

    return {"status": "left"}


# ─────────────────────────────────────────────
# WebSocket Endpoint
# ─────────────────────────────────────────────

@app.websocket("/ws/{code}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, code: str, player_id: str):
    """Persistent WebSocket connection per player per room."""
    await websocket.accept()

    if code not in connections:
        connections[code] = {}
    connections[code][player_id] = websocket

    # Confirm connection
    try:
        await websocket.send_json({"type": "connected", "player_id": player_id})
    except Exception:
        return

    try:
        while True:
            # Keep alive — client sends pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        # Cleanup
        if code in connections:
            connections[code].pop(player_id, None)
