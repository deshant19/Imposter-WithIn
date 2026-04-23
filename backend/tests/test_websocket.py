"""
test_websocket.py
=================
Tests for WebSocket connection behaviour and real-time notifications.

Uses FastAPI's built-in TestClient (sync) which handles WS via
starlette.testclient.  Each test that needs a room first calls the
REST endpoints via the AsyncClient, then opens WebSocket(s) via
the synchronous TestClient.
"""

import json
import threading
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: synchronous TestClient (for WebSocket)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sync_client():
    from main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def create_room_sync(sync_client, host_name="Alice"):
    resp = sync_client.post("/rooms", json={"host_name": host_name})
    assert resp.status_code == 200
    return resp.json()


def join_room_sync(sync_client, code, player_name):
    resp = sync_client.post(f"/rooms/{code}/join", json={"player_name": player_name})
    assert resp.status_code == 200
    return resp.json()


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket connection tests
# ─────────────────────────────────────────────────────────────────────────────

class TestWebSocketConnection:

    def test_websocket_accepts_connection(self, sync_client):
        room = create_room_sync(sync_client)
        with sync_client.websocket_connect(
            f"/ws/{room['room_code']}/{room['player_id']}"
        ) as ws:
            msg = ws.receive_json()
            assert msg["type"] == "connected"

    def test_connected_message_contains_player_id(self, sync_client):
        room = create_room_sync(sync_client)
        with sync_client.websocket_connect(
            f"/ws/{room['room_code']}/{room['player_id']}"
        ) as ws:
            msg = ws.receive_json()
            assert msg["player_id"] == room["player_id"]

    def test_ping_returns_pong(self, sync_client):
        room = create_room_sync(sync_client)
        with sync_client.websocket_connect(
            f"/ws/{room['room_code']}/{room['player_id']}"
        ) as ws:
            ws.receive_json()   # consume "connected"
            ws.send_text("ping")
            pong = ws.receive_text()
            assert pong == "pong"

    def test_connection_registered_in_memory(self, sync_client):
        """After connecting, the player_id should appear in connections dict."""
        import main as m
        room = create_room_sync(sync_client)
        with sync_client.websocket_connect(
            f"/ws/{room['room_code']}/{room['player_id']}"
        ) as ws:
            ws.receive_json()
            assert room["room_code"] in m.connections
            assert room["player_id"] in m.connections[room["room_code"]]

    def test_connection_removed_after_disconnect(self, sync_client):
        import main as m
        room = create_room_sync(sync_client)
        with sync_client.websocket_connect(
            f"/ws/{room['room_code']}/{room['player_id']}"
        ) as ws:
            ws.receive_json()
        # After the context manager exits, the connection must be cleaned up
        assert room["player_id"] not in m.connections.get(room["room_code"], {})


# ─────────────────────────────────────────────────────────────────────────────
# Notification broadcast tests
# ─────────────────────────────────────────────────────────────────────────────

class TestWebSocketNotifications:

    def test_existing_player_notified_when_new_player_joins(self, sync_client):
        """Alice's WebSocket should receive a player_joined event when Bob joins."""
        room = create_room_sync(sync_client, "Alice")
        code = room["room_code"]

        with sync_client.websocket_connect(f"/ws/{code}/{room['player_id']}") as alice_ws:
            alice_ws.receive_json()  # consume "connected"

            # Bob joins via REST
            sync_client.post(f"/rooms/{code}/join", json={"player_name": "Bob"})

            notification = alice_ws.receive_json()
            assert notification["type"] == "player_joined"

    def test_player_joined_notification_contains_player_name(self, sync_client):
        room = create_room_sync(sync_client, "Alice")
        code = room["room_code"]

        with sync_client.websocket_connect(f"/ws/{code}/{room['player_id']}") as alice_ws:
            alice_ws.receive_json()
            sync_client.post(f"/rooms/{code}/join", json={"player_name": "Bob"})
            notification = alice_ws.receive_json()
            assert notification["player_name"] == "Bob"

    def test_player_joined_notification_contains_updated_players_list(self, sync_client):
        room = create_room_sync(sync_client, "Alice")
        code = room["room_code"]

        with sync_client.websocket_connect(f"/ws/{code}/{room['player_id']}") as alice_ws:
            alice_ws.receive_json()
            sync_client.post(f"/rooms/{code}/join", json={"player_name": "Bob"})
            notification = alice_ws.receive_json()
            names = [p["name"] for p in notification["players"]]
            assert "Alice" in names and "Bob" in names

    def test_player_joined_notification_has_message_field(self, sync_client):
        room = create_room_sync(sync_client, "Alice")
        code = room["room_code"]

        with sync_client.websocket_connect(f"/ws/{code}/{room['player_id']}") as alice_ws:
            alice_ws.receive_json()
            sync_client.post(f"/rooms/{code}/join", json={"player_name": "Bob"})
            notification = alice_ws.receive_json()
            assert "message" in notification
            assert isinstance(notification["message"], str)
            assert len(notification["message"]) > 0

    def test_game_started_notification_delivered_via_websocket(self, sync_client):
        """Host should receive game_started via WS after calling /start."""
        room = create_room_sync(sync_client, "Alice")
        code, host_id = room["room_code"], room["player_id"]
        join_room_sync(sync_client, code, "Bob")
        join_room_sync(sync_client, code, "Carol")

        with sync_client.websocket_connect(f"/ws/{code}/{host_id}") as ws:
            ws.receive_json()   # connected
            sync_client.post(f"/rooms/{code}/start?player_id={host_id}")
            msg = ws.receive_json()
            assert msg["type"] == "game_started"

    def test_game_started_message_contains_assignment(self, sync_client):
        room = create_room_sync(sync_client, "Alice")
        code, host_id = room["room_code"], room["player_id"]
        join_room_sync(sync_client, code, "Bob")
        join_room_sync(sync_client, code, "Carol")

        with sync_client.websocket_connect(f"/ws/{code}/{host_id}") as ws:
            ws.receive_json()
            sync_client.post(f"/rooms/{code}/start?player_id={host_id}")
            msg = ws.receive_json()
            assert "assignment" in msg
            assert "is_imposter" in msg
            assert "total_players" in msg
            assert "imposter_count" in msg

    def test_game_reset_notification_broadcast(self, sync_client):
        """After /reset, all WS clients receive a game_reset event."""
        room = create_room_sync(sync_client, "Alice")
        code, host_id = room["room_code"], room["player_id"]
        join_room_sync(sync_client, code, "Bob")
        join_room_sync(sync_client, code, "Carol")

        with sync_client.websocket_connect(f"/ws/{code}/{host_id}") as ws:
            ws.receive_json()  # connected
            sync_client.post(f"/rooms/{code}/start?player_id={host_id}")
            ws.receive_json()  # game_started
            sync_client.post(f"/rooms/{code}/reset?player_id={host_id}")
            msg = ws.receive_json()
            assert msg["type"] == "game_reset"

    def test_game_reset_notification_contains_players(self, sync_client):
        room = create_room_sync(sync_client, "Alice")
        code, host_id = room["room_code"], room["player_id"]
        join_room_sync(sync_client, code, "Bob")
        join_room_sync(sync_client, code, "Carol")

        with sync_client.websocket_connect(f"/ws/{code}/{host_id}") as ws:
            ws.receive_json()
            sync_client.post(f"/rooms/{code}/start?player_id={host_id}")
            ws.receive_json()
            sync_client.post(f"/rooms/{code}/reset?player_id={host_id}")
            msg = ws.receive_json()
            assert "players" in msg
            assert len(msg["players"]) == 3

    def test_player_left_notification_broadcast(self, sync_client):
        room = create_room_sync(sync_client, "Alice")
        code, host_id = room["room_code"], room["player_id"]
        bob = join_room_sync(sync_client, code, "Bob")

        with sync_client.websocket_connect(f"/ws/{code}/{host_id}") as alice_ws:
            alice_ws.receive_json()  # connected
            # Bob joins (Alice gets notification)
            alice_ws.receive_json()  # player_joined

            sync_client.delete(f"/rooms/{code}/leave?player_id={bob['player_id']}")
            msg = alice_ws.receive_json()
            assert msg["type"] == "player_left"
            assert msg["player_name"] == "Bob"
