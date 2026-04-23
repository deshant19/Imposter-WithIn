"""
test_rooms_join_leave.py
========================
Integration tests for:
  POST   /rooms/{code}/join
  GET    /rooms/{code}
  DELETE /rooms/{code}/leave
"""

import pytest


class TestJoinRoom:

    @pytest.mark.asyncio
    async def test_success_returns_200(self, client, make_room):
        room = await make_room("Alice")
        resp = await client.post(f"/rooms/{room['room_code']}/join",
                                 json={"player_name": "Bob"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_schema(self, client, make_room):
        room = await make_room("Alice")
        data = (await client.post(f"/rooms/{room['room_code']}/join",
                                  json={"player_name": "Bob"})).json()
        for key in ("room_code", "player_id", "player_name", "players", "host_id"):
            assert key in data, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_joined_player_appears_in_list(self, client, make_room):
        room = await make_room("Alice")
        data = (await client.post(f"/rooms/{room['room_code']}/join",
                                  json={"player_name": "Bob"})).json()
        names = [p["name"] for p in data["players"]]
        assert "Bob" in names

    @pytest.mark.asyncio
    async def test_host_still_present_after_join(self, client, make_room):
        room = await make_room("Alice")
        data = (await client.post(f"/rooms/{room['room_code']}/join",
                                  json={"player_name": "Bob"})).json()
        names = [p["name"] for p in data["players"]]
        assert "Alice" in names

    @pytest.mark.asyncio
    async def test_player_count_increments(self, client, make_room):
        room = await make_room("Alice")
        data = (await client.post(f"/rooms/{room['room_code']}/join",
                                  json={"player_name": "Bob"})).json()
        assert len(data["players"]) == 2

    @pytest.mark.asyncio
    async def test_name_stripped_on_join(self, client, make_room):
        room = await make_room("Alice")
        data = (await client.post(f"/rooms/{room['room_code']}/join",
                                  json={"player_name": "  Carol  "})).json()
        names = [p["name"] for p in data["players"]]
        assert "Carol" in names

    @pytest.mark.asyncio
    async def test_join_nonexistent_room_returns_404(self, client):
        resp = await client.post("/rooms/ZZZZZZ/join", json={"player_name": "Alice"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_empty_name_returns_400(self, client, make_room):
        room = await make_room("Alice")
        resp = await client.post(f"/rooms/{room['room_code']}/join",
                                 json={"player_name": ""})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_duplicate_name_returns_400(self, client, make_room):
        room = await make_room("Alice")
        await client.post(f"/rooms/{room['room_code']}/join", json={"player_name": "Bob"})
        resp = await client.post(f"/rooms/{room['room_code']}/join", json={"player_name": "Bob"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_duplicate_name_case_insensitive(self, client, make_room):
        room = await make_room("Alice")
        await client.post(f"/rooms/{room['room_code']}/join", json={"player_name": "bob"})
        resp = await client.post(f"/rooms/{room['room_code']}/join", json={"player_name": "BOB"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_join_after_game_started_returns_400(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        code, host_id = ctx["room_code"], ctx["host_id"]
        await client.post(f"/rooms/{code}/start?player_id={host_id}")
        resp = await client.post(f"/rooms/{code}/join", json={"player_name": "Dave"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_room_cap_at_twenty_players(self, client, make_room):
        """The 21st join attempt must be rejected."""
        room = await make_room("P0")
        code = room["room_code"]
        for i in range(1, 20):
            r = await client.post(f"/rooms/{code}/join", json={"player_name": f"P{i}"})
            assert r.status_code == 200, f"Player {i} could not join (cap not yet reached)"
        # 21st player (index 20) should be rejected
        resp = await client.post(f"/rooms/{code}/join", json={"player_name": "Overflow"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_join_persists_to_file(self, client, make_room, isolated_storage):
        from main import load_rooms
        room = await make_room("Alice")
        await client.post(f"/rooms/{room['room_code']}/join", json={"player_name": "Bob"})
        persisted = load_rooms()[room["room_code"]]
        assert any(p["name"] == "Bob" for p in persisted["players"])


class TestGetRoom:

    @pytest.mark.asyncio
    async def test_returns_200_for_existing_room(self, client, make_room):
        room = await make_room("Alice")
        resp = await client.get(f"/rooms/{room['room_code']}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_schema(self, client, make_room):
        room = await make_room("Alice")
        data = (await client.get(f"/rooms/{room['room_code']}")).json()
        for key in ("code", "host_id", "players", "status", "imposter_count"):
            assert key in data

    @pytest.mark.asyncio
    async def test_initial_status_is_waiting(self, client, make_room):
        room = await make_room("Alice")
        data = (await client.get(f"/rooms/{room['room_code']}")).json()
        assert data["status"] == "waiting"

    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_code(self, client):
        resp = await client.get("/rooms/XYZABC")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_player_list_reflects_joins(self, client, make_room):
        room = await make_room("Alice")
        await client.post(f"/rooms/{room['room_code']}/join", json={"player_name": "Bob"})
        data = (await client.get(f"/rooms/{room['room_code']}")).json()
        assert len(data["players"]) == 2


class TestLeaveRoom:

    @pytest.mark.asyncio
    async def test_non_host_can_leave(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob"])
        bob_id = ctx["player_ids"][1]
        resp = await client.delete(
            f"/rooms/{ctx['room_code']}/leave?player_id={bob_id}"
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "left"

    @pytest.mark.asyncio
    async def test_player_removed_from_room(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob"])
        bob_id = ctx["player_ids"][1]
        await client.delete(f"/rooms/{ctx['room_code']}/leave?player_id={bob_id}")
        data = (await client.get(f"/rooms/{ctx['room_code']}")).json()
        names = [p["name"] for p in data["players"]]
        assert "Bob" not in names

    @pytest.mark.asyncio
    async def test_host_leaving_promotes_next_player(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        alice_id = ctx["host_id"]
        await client.delete(f"/rooms/{ctx['room_code']}/leave?player_id={alice_id}")
        data = (await client.get(f"/rooms/{ctx['room_code']}")).json()
        # The new host should be Bob (first remaining player)
        assert data["host_id"] != alice_id

    @pytest.mark.asyncio
    async def test_last_player_leaving_deletes_room(self, client, make_room):
        room = await make_room("Alice")
        resp = await client.delete(
            f"/rooms/{room['room_code']}/leave?player_id={room['player_id']}"
        )
        assert resp.json()["status"] == "room_deleted"
        # Room must no longer be reachable
        get_resp = await client.get(f"/rooms/{room['room_code']}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_leave_nonexistent_room_returns_404(self, client):
        resp = await client.delete("/rooms/XXXXXX/leave?player_id=p_999")
        assert resp.status_code == 404
