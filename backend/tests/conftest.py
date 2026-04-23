"""
conftest.py — Shared fixtures for all backend tests.

Provides:
  - Isolated temp file storage (never touches real rooms.json)
  - A fresh AsyncClient for every test
  - Factory helpers: make_room(), populate_room()
  - WebSocket context manager
"""

import json
import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# ── patch storage BEFORE importing the app ──────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """
    Redirect all file I/O to a throwaway temp directory.
    Runs automatically for every test (autouse=True).
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    rooms_file = str(data_dir / "rooms.json")

    import main as m
    monkeypatch.setattr(m, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(m, "ROOMS_FILE", rooms_file)

    # Start each test with an empty store and empty WS connections
    m.connections.clear()
    yield rooms_file

    # Cleanup connections after each test
    m.connections.clear()


@pytest_asyncio.fixture
async def client():
    """Fresh AsyncClient per test, wired to the ASGI app."""
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ── Factory helpers ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def make_room(client):
    """
    Async factory: creates a room and returns full response data.
    Usage:  data = await make_room("Alice")
    """
    async def _factory(host_name: str = "Alice"):
        resp = await client.post("/rooms", json={"host_name": host_name})
        assert resp.status_code == 200, resp.text
        return resp.json()
    return _factory


@pytest_asyncio.fixture
async def room_with_players(client, make_room):
    """
    Creates a room with a configurable set of named players already joined.
    Returns dict with keys: room_code, host_id, host_player_id, player_ids, players.

    Usage:
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
    """
    async def _factory(names: list[str]):
        assert len(names) >= 1
        host_data = await make_room(names[0])
        code = host_data["room_code"]
        player_ids = [host_data["player_id"]]

        for name in names[1:]:
            r = await client.post(f"/rooms/{code}/join", json={"player_name": name})
            assert r.status_code == 200, r.text
            player_ids.append(r.json()["player_id"])

        return {
            "room_code": code,
            "host_id": host_data["player_id"],
            "player_ids": player_ids,
            "names": names,
        }
    return _factory
