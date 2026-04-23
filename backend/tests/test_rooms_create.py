"""
test_rooms_create.py
====================
Integration tests for:
  GET  /health
  POST /rooms   (create a room)

Each test uses the isolated_storage + AsyncClient fixtures from conftest.py,
so no real rooms.json is ever touched.
"""

import pytest
import pytest_asyncio


# ─────────────────────────────────────────────────────────────────────────────
# /health
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthEndpoint:

    @pytest.mark.asyncio
    async def test_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_body(self, client):
        data = (await client.get("/health")).json()
        assert data["status"] == "ok"
        assert data["service"] == "Imposter Within"

    @pytest.mark.asyncio
    async def test_content_type_is_json(self, client):
        resp = await client.get("/health")
        assert "application/json" in resp.headers["content-type"]


# ─────────────────────────────────────────────────────────────────────────────
# POST /rooms
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateRoom:

    @pytest.mark.asyncio
    async def test_success_returns_200(self, client):
        resp = await client.post("/rooms", json={"host_name": "Alice"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_contains_room_code(self, client):
        data = (await client.post("/rooms", json={"host_name": "Alice"})).json()
        assert "room_code" in data
        code = data["room_code"]
        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isupper()

    @pytest.mark.asyncio
    async def test_response_contains_player_id(self, client):
        data = (await client.post("/rooms", json={"host_name": "Alice"})).json()
        assert "player_id" in data
        assert data["player_id"].startswith("p_")

    @pytest.mark.asyncio
    async def test_response_contains_player_name(self, client):
        data = (await client.post("/rooms", json={"host_name": "Alice"})).json()
        assert data["player_name"] == "Alice"

    @pytest.mark.asyncio
    async def test_name_is_stripped_of_whitespace(self, client):
        data = (await client.post("/rooms", json={"host_name": "  Bob  "})).json()
        assert data["player_name"] == "Bob"

    @pytest.mark.asyncio
    async def test_room_is_persisted_to_file(self, client, isolated_storage):
        from main import load_rooms
        data = (await client.post("/rooms", json={"host_name": "Alice"})).json()
        rooms = load_rooms()
        assert data["room_code"] in rooms

    @pytest.mark.asyncio
    async def test_persisted_room_has_correct_host(self, client, isolated_storage):
        from main import load_rooms
        data = (await client.post("/rooms", json={"host_name": "Alice"})).json()
        room = load_rooms()[data["room_code"]]
        assert room["host_id"] == data["player_id"]

    @pytest.mark.asyncio
    async def test_persisted_room_status_is_waiting(self, client, isolated_storage):
        from main import load_rooms
        data = (await client.post("/rooms", json={"host_name": "Alice"})).json()
        room = load_rooms()[data["room_code"]]
        assert room["status"] == "waiting"

    @pytest.mark.asyncio
    async def test_persisted_room_has_one_player(self, client, isolated_storage):
        from main import load_rooms
        data = (await client.post("/rooms", json={"host_name": "Alice"})).json()
        room = load_rooms()[data["room_code"]]
        assert len(room["players"]) == 1
        assert room["players"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_empty_name_returns_400(self, client):
        resp = await client.post("/rooms", json={"host_name": ""})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_whitespace_only_name_returns_400(self, client):
        resp = await client.post("/rooms", json={"host_name": "   "})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_host_name_field_returns_422(self, client):
        resp = await client.post("/rooms", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_two_rooms_get_different_codes(self, client):
        code1 = (await client.post("/rooms", json={"host_name": "A"})).json()["room_code"]
        code2 = (await client.post("/rooms", json={"host_name": "B"})).json()["room_code"]
        assert code1 != code2

    @pytest.mark.asyncio
    async def test_unicode_name_accepted(self, client):
        resp = await client.post("/rooms", json={"host_name": "José"})
        assert resp.status_code == 200
        assert resp.json()["player_name"] == "José"

    @pytest.mark.asyncio
    async def test_long_name_accepted(self, client):
        name = "A" * 50
        resp = await client.post("/rooms", json={"host_name": name})
        # Application does not enforce a length limit — just verifies non-empty
        assert resp.status_code == 200
