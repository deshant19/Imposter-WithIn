"""
test_game_flow.py
=================
Integration tests for:
  POST /rooms/{code}/start
  POST /rooms/{code}/reset

Covers permissions, state transitions, role-assignment correctness,
and the full start→reset→start lifecycle.
"""

import pytest
from main import load_rooms, WORD_LIST


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def start_game(client, code, host_id):
    return await client.post(f"/rooms/{code}/start?player_id={host_id}")


async def reset_game(client, code, host_id):
    return await client.post(f"/rooms/{code}/reset?player_id={host_id}")


# ─────────────────────────────────────────────────────────────────────────────
# Start Game — happy paths
# ─────────────────────────────────────────────────────────────────────────────

class TestStartGame:

    @pytest.mark.asyncio
    async def test_host_can_start_with_minimum_players(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        resp = await start_game(client, ctx["room_code"], ctx["host_id"])
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_contains_status_started(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        data = (await start_game(client, ctx["room_code"], ctx["host_id"])).json()
        assert data["status"] == "started"

    @pytest.mark.asyncio
    async def test_response_contains_imposter_count(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        data = (await start_game(client, ctx["room_code"], ctx["host_id"])).json()
        assert "imposter_count" in data
        assert data["imposter_count"] == 1  # 3 players → 1 imposter

    @pytest.mark.asyncio
    async def test_room_status_changes_to_playing(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        assert room["status"] == "playing"

    @pytest.mark.asyncio
    async def test_assignments_stored_for_all_players(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        assert len(room["assignments"]) == 3

    @pytest.mark.asyncio
    async def test_word_stored_in_room(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        assert room["word"] in WORD_LIST

    @pytest.mark.asyncio
    async def test_exactly_one_imposter_in_three_player_game(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["A", "B", "C"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        imposters = [v for v in room["assignments"].values() if v == "IMPOSTER"]
        assert len(imposters) == 1

    @pytest.mark.asyncio
    async def test_exactly_two_imposters_in_five_player_game(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["A", "B", "C", "D", "E"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        imposters = [v for v in room["assignments"].values() if v == "IMPOSTER"]
        assert len(imposters) == 2

    @pytest.mark.asyncio
    async def test_all_non_imposters_get_same_word(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["A", "B", "C", "D"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        agent_words = {v for v in room["assignments"].values() if v != "IMPOSTER"}
        assert len(agent_words) == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize("player_count,expected_imposters", [
        (3, 1), (4, 1), (5, 2), (9, 2), (10, 3), (14, 3), (15, 4),
    ])
    async def test_imposter_count_per_player_count(
        self, client, room_with_players, isolated_storage,
        player_count, expected_imposters
    ):
        names = [f"P{i}" for i in range(player_count)]
        ctx = await room_with_players(names)
        await start_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        actual = sum(1 for v in room["assignments"].values() if v == "IMPOSTER")
        assert actual == expected_imposters


# ─────────────────────────────────────────────────────────────────────────────
# Start Game — error / edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestStartGameErrors:

    @pytest.mark.asyncio
    async def test_non_host_cannot_start(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        non_host_id = ctx["player_ids"][1]   # Bob
        resp = await start_game(client, ctx["room_code"], non_host_id)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_start_with_only_two_players_returns_400(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob"])
        resp = await start_game(client, ctx["room_code"], ctx["host_id"])
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_start_with_one_player_returns_400(self, client, make_room):
        room = await make_room("Alice")
        resp = await start_game(client, room["room_code"], room["player_id"])
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_start_already_playing_room(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        resp = await start_game(client, ctx["room_code"], ctx["host_id"])
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_start_nonexistent_room_returns_404(self, client):
        resp = await client.post("/rooms/ZZZZZZ/start?player_id=p_fake")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_room_remains_waiting_after_failed_start(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["Alice", "Bob"])
        await start_game(client, ctx["room_code"], ctx["host_id"])  # should fail
        room = load_rooms()[ctx["room_code"]]
        assert room["status"] == "waiting"


# ─────────────────────────────────────────────────────────────────────────────
# Reset Game
# ─────────────────────────────────────────────────────────────────────────────

class TestResetGame:

    @pytest.mark.asyncio
    async def test_host_can_reset(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        resp = await reset_game(client, ctx["room_code"], ctx["host_id"])
        assert resp.status_code == 200
        assert resp.json()["status"] == "reset"

    @pytest.mark.asyncio
    async def test_room_status_returns_to_waiting(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        await reset_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        assert room["status"] == "waiting"

    @pytest.mark.asyncio
    async def test_assignments_cleared_after_reset(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        await reset_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        assert room["assignments"] == {}

    @pytest.mark.asyncio
    async def test_word_cleared_after_reset(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        await reset_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        assert room["word"] == ""

    @pytest.mark.asyncio
    async def test_players_preserved_after_reset(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        await reset_game(client, ctx["room_code"], ctx["host_id"])
        room = load_rooms()[ctx["room_code"]]
        assert len(room["players"]) == 3

    @pytest.mark.asyncio
    async def test_non_host_cannot_reset(self, client, room_with_players):
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        non_host = ctx["player_ids"][1]
        resp = await reset_game(client, ctx["room_code"], non_host)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_reset_nonexistent_room_returns_404(self, client):
        resp = await client.post("/rooms/ZZZZZZ/reset?player_id=p_fake")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_game_can_start_again_after_reset(self, client, room_with_players, isolated_storage):
        """Full lifecycle: start → reset → start again."""
        ctx = await room_with_players(["Alice", "Bob", "Carol"])
        await start_game(client, ctx["room_code"], ctx["host_id"])
        await reset_game(client, ctx["room_code"], ctx["host_id"])
        resp = await start_game(client, ctx["room_code"], ctx["host_id"])
        assert resp.status_code == 200
        room = load_rooms()[ctx["room_code"]]
        assert room["status"] == "playing"
