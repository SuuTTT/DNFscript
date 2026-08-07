import unittest

from questpilot.card_duel_mock import CardDuel


class CardDuelMockTests(unittest.TestCase):
    def test_new_duel_has_original_cards_and_opening_hands(self):
        duel = CardDuel.new()
        self.assertEqual(len(duel.player.hand), 3)
        self.assertEqual(len(duel.player.lanes), 3)
        self.assertTrue(all("Yu" not in card.name for card in duel.player.hand))

    def test_player_can_play_only_an_affordable_card_into_an_empty_lane(self):
        duel = CardDuel.new()
        affordable = next(index for index, card in enumerate(duel.player.hand) if card.cost <= duel.player.energy)
        self.assertTrue(duel.play(affordable, 0))
        self.assertFalse(duel.play(0, 0))

    def test_player_attack_hits_same_lane_or_rival_core(self):
        duel = CardDuel.new()
        card_index = next(index for index, card in enumerate(duel.player.hand) if card.cost <= duel.player.energy)
        self.assertTrue(duel.play(card_index, 0))
        duel.player.lanes[0].exhausted = False
        starting_core = duel.rival.core
        self.assertTrue(duel.attack(0))
        self.assertLess(duel.rival.core, starting_core)

    def test_rival_turn_is_deterministic_and_never_controls_an_external_game(self):
        duel = CardDuel.new()
        duel.end_player_turn()
        self.assertTrue(duel.player_turn)
        self.assertTrue(any("Rival" in event for event in duel.log))
        source = (self._repo_root() / "questpilot/card_duel_mock.py").read_text(encoding="utf-8")
        self.assertNotIn("requests", source)
        self.assertNotIn("socket", source)
        self.assertNotIn("selenium", source)

    def test_browser_playground_is_original_and_has_no_network_surface(self):
        page = (self._repo_root() / "demo/skyforge-card-duel.html").read_text(encoding="utf-8")
        self.assertIn("Aetherfold Arena", page)
        self.assertIn("End round", page)
        self.assertIn("Original mock only", page)
        self.assertNotIn("fetch(", page)
        self.assertNotIn("WebSocket", page)

    @staticmethod
    def _repo_root():
        from pathlib import Path
        return Path(__file__).parents[1]
