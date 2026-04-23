"""
test_game_logic.py
==================
Pure unit tests for game-logic functions that require NO HTTP layer.
These are the fastest tests in the suite — run them first.

Covers:
  • get_imposter_count() – every boundary in the spec
  • assign_roles()       – distribution, word uniqueness, IMPOSTER count
  • generate_room_code() – format contract
  • load_rooms / save_rooms – JSON round-trip
"""

import json
import os
import pytest

from main import (
    get_imposter_count,
    assign_roles,
    generate_room_code,
    load_rooms,
    save_rooms,
    WORD_LIST,
)


# ─────────────────────────────────────────────────────────────────────────────
# get_imposter_count
# ─────────────────────────────────────────────────────────────────────────────

class TestGetImposterCount:
    """Validates the piecewise imposter-scaling rule from the spec."""

    # Boundary: 3–4 players → exactly 1 imposter
    @pytest.mark.parametrize("n", [3, 4])
    def test_three_to_four_players_one_imposter(self, n):
        assert get_imposter_count(n) == 1

    # Boundary: 5–9 players → exactly 2 imposters
    @pytest.mark.parametrize("n", [5, 6, 7, 8, 9])
    def test_five_to_nine_players_two_imposters(self, n):
        assert get_imposter_count(n) == 2

    # Boundary: 10–14 players → exactly 3 imposters
    @pytest.mark.parametrize("n", [10, 11, 12, 13, 14])
    def test_ten_to_fourteen_players_three_imposters(self, n):
        assert get_imposter_count(n) == 3

    # Boundary: 15–19 players → exactly 4 imposters
    @pytest.mark.parametrize("n", [15, 16, 17, 18, 19])
    def test_fifteen_to_nineteen_players_four_imposters(self, n):
        assert get_imposter_count(n) == 4

    # Each jump at a multiple-of-5 threshold increases count by 1
    def test_imposter_count_increases_at_multiples_of_five(self):
        jumps = [(4, 5), (9, 10), (14, 15)]
        for before, at in jumps:
            assert get_imposter_count(at) == get_imposter_count(before) + 1, (
                f"Expected count to increase between n={before} and n={at}"
            )

    # Imposters must always be a strict minority
    @pytest.mark.parametrize("n", range(3, 20))
    def test_imposters_always_minority(self, n):
        count = get_imposter_count(n)
        assert count < n, f"Imposters ({count}) must be fewer than total players ({n})"

    # Return type must be int
    @pytest.mark.parametrize("n", [3, 10, 19])
    def test_return_type_is_int(self, n):
        assert isinstance(get_imposter_count(n), int)


# ─────────────────────────────────────────────────────────────────────────────
# assign_roles
# ─────────────────────────────────────────────────────────────────────────────

def _make_players(n: int) -> list[dict]:
    return [{"id": f"p{i}", "name": f"Player{i}"} for i in range(n)]


class TestAssignRoles:

    def test_returns_three_values(self):
        players = _make_players(3)
        result = assign_roles(players)
        assert len(result) == 3, "assign_roles must return (assignments, word, imposter_count)"

    def test_assignments_covers_all_players(self):
        players = _make_players(5)
        assignments, _, _ = assign_roles(players)
        assert set(assignments.keys()) == {p["id"] for p in players}

    def test_word_is_from_word_list(self):
        players = _make_players(4)
        _, word, _ = assign_roles(players)
        assert word in WORD_LIST

    def test_non_imposters_all_get_same_word(self):
        players = _make_players(5)
        assignments, word, _ = assign_roles(players)
        agent_words = {v for v in assignments.values() if v != "IMPOSTER"}
        assert len(agent_words) == 1
        assert word in agent_words

    @pytest.mark.parametrize("n", [3, 4, 5, 9, 10, 14, 15, 19])
    def test_imposter_count_matches_spec(self, n):
        players = _make_players(n)
        assignments, _, imposter_count = assign_roles(players)
        actual_imposters = sum(1 for v in assignments.values() if v == "IMPOSTER")
        expected = get_imposter_count(n)
        assert actual_imposters == expected
        assert imposter_count == expected

    def test_at_least_one_non_imposter_always(self):
        """Even in the maximum case (19 players, 4 imposters), agents exist."""
        players = _make_players(19)
        assignments, _, _ = assign_roles(players)
        agents = [v for v in assignments.values() if v != "IMPOSTER"]
        assert len(agents) >= 1

    def test_randomness_produces_different_imposters(self):
        """Over many runs the same game produces varied imposter picks."""
        players = _make_players(10)
        imposter_sets = set()
        for _ in range(30):
            assignments, _, _ = assign_roles(players)
            imposter_set = frozenset(k for k, v in assignments.items() if v == "IMPOSTER")
            imposter_sets.add(imposter_set)
        # With 10 players and 3 imposters C(10,3)=120 combos, expect > 1 in 30 draws
        assert len(imposter_sets) > 1, "assign_roles appears to always pick the same imposters"

    def test_randomness_produces_different_words(self):
        """Over many runs the chosen word varies."""
        players = _make_players(4)
        words = {assign_roles(players)[1] for _ in range(50)}
        assert len(words) > 1, "assign_roles appears to always pick the same word"


# ─────────────────────────────────────────────────────────────────────────────
# generate_room_code
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateRoomCode:

    def test_length_is_six(self):
        assert len(generate_room_code()) == 6

    def test_all_uppercase_ascii_letters(self):
        code = generate_room_code()
        assert code.isalpha() and code.isupper()

    def test_codes_are_random(self):
        codes = {generate_room_code() for _ in range(100)}
        # With 26^6 ≈ 308 million possibilities, 100 draws must all differ
        assert len(codes) == 100


# ─────────────────────────────────────────────────────────────────────────────
# load_rooms / save_rooms (file I/O)
# ─────────────────────────────────────────────────────────────────────────────

class TestFileStorage:

    def test_save_and_load_roundtrip(self, isolated_storage):
        data = {"ABCDEF": {"code": "ABCDEF", "players": [], "status": "waiting"}}
        save_rooms(data)
        loaded = load_rooms()
        assert loaded == data

    def test_load_returns_empty_dict_when_file_missing(self, isolated_storage, monkeypatch):
        import main as m
        monkeypatch.setattr(m, "ROOMS_FILE", "/tmp/nonexistent_file_xyz.json")
        assert load_rooms() == {}

    def test_load_returns_empty_dict_on_corrupt_json(self, isolated_storage):
        import main as m
        with open(m.ROOMS_FILE, "w") as f:
            f.write("{this is not valid JSON!!!}")
        assert load_rooms() == {}

    def test_save_overwrites_existing_data(self, isolated_storage):
        save_rooms({"OLD": {}})
        save_rooms({"NEW": {}})
        assert load_rooms() == {"NEW": {}}

    def test_save_creates_valid_json(self, isolated_storage):
        import main as m
        save_rooms({"X": {"key": "value", "num": 42}})
        with open(m.ROOMS_FILE) as f:
            raw = f.read()
        parsed = json.loads(raw)
        assert parsed["X"]["num"] == 42

    def test_multiple_rooms_persist_together(self, isolated_storage):
        rooms = {f"ROOM{i:02d}": {"id": i} for i in range(5)}
        save_rooms(rooms)
        loaded = load_rooms()
        assert len(loaded) == 5
        for key in rooms:
            assert key in loaded
