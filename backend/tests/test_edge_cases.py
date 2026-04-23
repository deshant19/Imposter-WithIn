"""
test_edge_cases.py
==================
Edge-case, boundary-value, and concurrency-style tests that do not
fit neatly into the other modules.

Topics:
  - Concurrent room creation (unique code collision avoidance)
  - Rapid start → reset → start cycles
  - Partial state corruption recovery (missing keys in rooms.json)
  - Input boundary values (name length, code format)
  - Idempotent DELETE behaviour
  - Multiple rooms coexist independently
"""

import asyncio
import json
import pytest
from main import load_rooms, save_rooms, get_imposter_count


# ─────────────────────────────────────────────────────────────────────────────
# Concurrent room creation
# ─────────────────────────────────────────────────────────────────────────────

class TestConcurrentRoomCreation:

    @pytest.mark.asyncio
    async def test_twenty_simultaneous_room_creations_produce_unique_codes(self, client):
        tasks = [client.post("/rooms", json={"host_name": f"Host{i}"}) for i in range(20)]
        responses = await asyncio.gather(*tasks)
        codes = [r.json()["room_code"] for r in responses if r.status_code == 200]
        assert len(codes) == len(set(codes)), "Duplicate room codes detected under concurrency"

    @pytest.mark.asyncio
    async def test_all_concurrent_rooms_persisted(self, client, isolated_storage):
        tasks = [client.post("/rooms", json={"host_name": f"H{i}"}) for i in range(10)]
        responses = await asyncio.gather(*tasks)
        rooms = load_rooms()
        assert len(rooms) == 10


# ─────────────────────────────────────────────────────────────────────────────
# Multiple rooms coexist
# ─────────────────────────────────────────────────────────────────────────────

class TestMultipleRooms:

    @pytest.mark.asyncio
    async def test_actions_in_one_room_do_not_affect_another(
        self, client, room_with_players
    ):
        ctx_a = await room_with_players(["Alice", "Bob", "Carol"])
        ctx_b = await room_with_players(["X", "Y", "Z"])

        # Start game in room A
        await client.post(
            f"/rooms/{ctx_a['room_code']}/start?player_id={ctx_a['host_id']}"
        )

        # Room B should still be in "waiting"
        resp_b = await client.get(f"/rooms/{ctx_b['room_code']}")
        assert resp_b.json()["status"] == "waiting"

    @pytest.mark.asyncio
    async def test_same_player_name_allowed_in_different_rooms(self, client, make_room):
        room_a = await make_room("Alice")
        room_b = await make_room("Host")
        resp = await client.post(
            f"/rooms/{room_b['room_code']}/join", json={"player_name": "Alice"}
        )
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Rapid lifecycle
# ─────────────────────────────────────────────────────────────────────────────

class TestRapidLifecycle:

    @pytest.mark.asyncio
    async def test_five_start_reset_cycles(self, client, room_with_players, isolated_storage):
        ctx = await room_with_players(["A", "B", "C"])
        code, host = ctx["room_code"], ctx["host_id"]
        for cycle in range(5):
            start = await client.post(f"/rooms/{code}/start?player_id={host}")
            assert start.status_code == 200, f"Cycle {cycle}: start failed"
            reset = await client.post(f"/rooms/{code}/reset?player_id={host}")
            assert reset.status_code == 200, f"Cycle {cycle}: reset failed"
        room = load_rooms()[code]
        assert room["status"] == "waiting"

    @pytest.mark.asyncio
    async def test_different_word_may_be_chosen_across_cycles(self, client, room_with_players, isolated_storage):
        """Over 20 cycles the chosen secret word should vary (not always the same)."""
        ctx = await room_with_players(["A", "B", "C"])
        code, host = ctx["room_code"], ctx["host_id"]
        words = set()
        for _ in range(20):
            await client.post(f"/rooms/{code}/start?player_id={host}")
            words.add(load_rooms()[code]["word"])
            await client.post(f"/rooms/{code}/reset?player_id={host}")
        assert len(words) > 1, "Word assignment appears to not be random across cycles"


# ─────────────────────────────────────────────────────────────────────────────
# Partial / corrupted room state
# ─────────────────────────────────────────────────────────────────────────────

class TestCorruptedStateRecovery:

    def test_load_rooms_tolerates_corrupt_json(self, isolated_storage):
        import main as m
        with open(m.ROOMS_FILE, "w") as f:
            f.write("NOT JSON {{{ broken")
        result = load_rooms()
        assert result == {}

    def test_load_rooms_tolerates_empty_file(self, isolated_storage):
        import main as m
        with open(m.ROOMS_FILE, "w") as f:
            f.write("")
        result = load_rooms()
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_room_with_missing_imposter_count_key(self, client, isolated_storage):
        """Rooms created by older versions may lack imposter_count; should default to 0."""
        import main as m
        rooms = load_rooms()
        rooms["LEGACY"] = {
            "code": "LEGACY",
            "host_id": "p_1",
            "players": [{"id": "p_1", "name": "OldUser"}],
            "status": "waiting",
            "assignments": {},
            "word": "",
            # intentionally omitting "imposter_count"
            "created_at": 0,
        }
        save_rooms(rooms)
        resp = await client.get("/rooms/LEGACY")
        assert resp.status_code == 200
        assert resp.json().get("imposter_count", 0) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Input boundary values
# ─────────────────────────────────────────────────────────────────────────────

class TestInputBoundaries:

    @pytest.mark.asyncio
    async def test_room_code_case_sensitivity_on_join(self, client, make_room):
        """The path param is passed as-is; test that lowercase code fails (not found)."""
        room = await make_room("Alice")
        lower_code = room["room_code"].lower()
        resp = await client.post(f"/rooms/{lower_code}/join", json={"player_name": "Bob"})
        # lowercase code won't match the stored UPPERCASE code
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_player_name_with_spaces_accepted(self, client, make_room):
        room = await make_room("Alice")
        resp = await client.post(
            f"/rooms/{room['room_code']}/join",
            json={"player_name": "John Doe"},
        )
        assert resp.status_code == 200
        assert any(p["name"] == "John Doe" for p in resp.json()["players"])

    @pytest.mark.asyncio
    async def test_player_name_single_character_accepted(self, client, make_room):
        room = await make_room("Alice")
        resp = await client.post(
            f"/rooms/{room['room_code']}/join", json={"player_name": "X"}
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_create_room_with_numeric_name(self, client):
        resp = await client.post("/rooms", json={"host_name": "1234"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_start_query_param_missing_returns_422(self, client, room_with_players):
        ctx = await room_with_players(["A", "B", "C"])
        resp = await client.post(f"/rooms/{ctx['room_code']}/start")  # no ?player_id
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_reset_query_param_missing_returns_422(self, client, room_with_players):
        ctx = await room_with_players(["A", "B", "C"])
        resp = await client.post(f"/rooms/{ctx['room_code']}/reset")
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# Imposter-minority invariant across all valid player counts
# ─────────────────────────────────────────────────────────────────────────────

class TestImposterMinorityInvariant:

    @pytest.mark.parametrize("n", range(3, 20))
    def test_imposters_never_equal_or_exceed_agents(self, n):
        imposters = get_imposter_count(n)
        agents = n - imposters
        assert imposters < agents, (
            f"n={n}: imposters={imposters} ≥ agents={agents}; game would be unwinnable"
        )
