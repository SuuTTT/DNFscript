"""Original, deterministic card-duel sandbox rules for Skyforge practice only.

This is a compact rules model for an original browser playground.  It has no
game-client integration, network I/O, credentials, capture, or input control.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DuelCard:
    name: str
    cost: int
    power: int
    guard: int


CARD_LIBRARY = {
    "ember_scribe": DuelCard("Ember Scribe", 1, 2, 1),
    "tide_aegis": DuelCard("Tide Aegis", 2, 1, 4),
    "glasswing": DuelCard("Glasswing", 2, 3, 1),
    "rootwarden": DuelCard("Rootwarden", 3, 3, 4),
    "star_pylon": DuelCard("Star Pylon", 4, 5, 3),
}


@dataclass
class DuelUnit:
    card: DuelCard
    guard: int
    exhausted: bool = True

    @classmethod
    def summon(cls, card: DuelCard) -> "DuelUnit":
        return cls(card, card.guard)


@dataclass
class DuelSide:
    core: int = 20
    energy: int = 1
    max_energy: int = 1
    deck: list[DuelCard] = field(default_factory=list)
    hand: list[DuelCard] = field(default_factory=list)
    lanes: list[DuelUnit | None] = field(default_factory=lambda: [None, None, None])

    def draw(self) -> DuelCard | None:
        if not self.deck:
            return None
        card = self.deck.pop(0)
        self.hand.append(card)
        return card


@dataclass
class CardDuel:
    """A manual, three-lane original card duel with a deterministic sparring side."""

    player: DuelSide
    rival: DuelSide
    player_turn: bool = True
    over: bool = False
    log: list[str] = field(default_factory=list)

    @classmethod
    def new(cls) -> "CardDuel":
        deck = [
            CARD_LIBRARY[key]
            for key in ("ember_scribe", "glasswing", "tide_aegis", "rootwarden", "star_pylon")
            for _ in range(2)
        ]
        player, rival = DuelSide(deck=deck.copy()), DuelSide(deck=list(reversed(deck)))
        for _ in range(3):
            player.draw()
            rival.draw()
        return cls(player, rival, log=["Aetherfold practice duel started."])

    def play(self, hand_index: int, lane: int, *, rival: bool = False) -> bool:
        side = self.rival if rival else self.player
        if self.over or lane not in range(3) or side.lanes[lane] is not None or hand_index not in range(len(side.hand)):
            return False
        card = side.hand[hand_index]
        if card.cost > side.energy:
            return False
        side.energy -= card.cost
        side.hand.pop(hand_index)
        side.lanes[lane] = DuelUnit.summon(card)
        self.log.append(f"{'Rival' if rival else 'Player'} summoned {card.name} on lane {lane + 1}.")
        return True

    def attack(self, lane: int) -> bool:
        """The player attacks the opposing unit in the same lane, or the rival core."""
        if self.over or not self.player_turn or lane not in range(3):
            return False
        attacker = self.player.lanes[lane]
        if attacker is None or attacker.exhausted:
            return False
        attacker.exhausted = True
        defender = self.rival.lanes[lane]
        if defender is None:
            self.rival.core -= attacker.card.power
            self.log.append(f"{attacker.card.name} struck the rival core for {attacker.card.power}.")
        else:
            defender.guard -= attacker.card.power
            attacker.guard -= defender.card.power
            self.log.append(f"Lane {lane + 1}: {attacker.card.name} exchanged with {defender.card.name}.")
            if defender.guard <= 0:
                self.rival.lanes[lane] = None
            if attacker.guard <= 0:
                self.player.lanes[lane] = None
        self._finish_if_needed()
        return True

    def begin_player_turn(self) -> None:
        self.player_turn = True
        self.player.max_energy = min(6, self.player.max_energy + 1)
        self.player.energy = self.player.max_energy
        self.player.draw()
        for unit in self.player.lanes:
            if unit:
                unit.exhausted = False
        self.log.append("Player turn: energy renewed and a card drawn.")

    def end_player_turn(self) -> None:
        if self.over:
            return
        self.player_turn = False
        self._rival_turn()
        if not self.over:
            self.begin_player_turn()

    def _rival_turn(self) -> None:
        self.rival.max_energy = min(6, self.rival.max_energy + 1)
        self.rival.energy = self.rival.max_energy
        self.rival.draw()
        for unit in self.rival.lanes:
            if unit:
                unit.exhausted = False
        empty = next((index for index, unit in enumerate(self.rival.lanes) if unit is None), None)
        affordable = [(index, card) for index, card in enumerate(self.rival.hand) if card.cost <= self.rival.energy]
        if empty is not None and affordable:
            index, _ = max(affordable, key=lambda item: (item[1].power, item[1].guard, -item[0]))
            self.play(index, empty, rival=True)
        for lane, attacker in enumerate(list(self.rival.lanes)):
            if attacker is None:
                continue
            defender = self.player.lanes[lane]
            if defender is None:
                self.player.core -= attacker.card.power
                self.log.append(f"Rival {attacker.card.name} struck your core for {attacker.card.power}.")
            else:
                defender.guard -= attacker.card.power
                attacker.guard -= defender.card.power
                self.log.append(f"Rival battle on lane {lane + 1}.")
                if defender.guard <= 0:
                    self.player.lanes[lane] = None
                if attacker.guard <= 0:
                    self.rival.lanes[lane] = None
            self._finish_if_needed()
            if self.over:
                return
        self.log.append("Rival practice turn ended.")

    def _finish_if_needed(self) -> None:
        if self.player.core <= 0 or self.rival.core <= 0:
            self.over = True
            self.log.append("Practice duel ended.")
