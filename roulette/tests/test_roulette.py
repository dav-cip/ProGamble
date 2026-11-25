"""Tests de la logique du jeu (a lancer sur PC : python3 tests/test_roulette.py)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import roulette
from roulette import Game, color_of, RED_NUMBERS


def test_colors():
    assert color_of(0) == "green"
    assert len(RED_NUMBERS) == 18
    assert sum(1 for n in range(1, 37) if color_of(n) == "black") == 18
    assert color_of(1) == "red" and color_of(2) == "black" and color_of(36) == "red"


def test_payouts():
    g = Game()
    g.bet_index = 0                      # ROUGE
    assert g.start_spin() and g.balance == 490
    won, net = g.finish_spin(1)          # 1 est rouge
    assert won and net == 10 and g.balance == 510
    g.bet_index = 1                      # NOIR
    g.start_spin()
    won, net = g.finish_spin(1)
    assert not won and net == -10 and g.balance == 500
    g.bet_index = 3 + 17                 # numero 17
    g.start_spin()
    won, net = g.finish_spin(17)
    assert won and net == 350 and g.balance == 850


def test_zero_loses_on_colors():
    g = Game()
    for idx in (0, 1):
        g.bet_index = idx
        g.start_spin()
        won, _ = g.finish_spin(0)
        assert not won


def test_green():
    g = Game()
    g.bet_index = 2
    g.start_spin()
    assert g.finish_spin(0)[0] and not g.wins(5)


def test_cannot_overbet():
    g = Game()
    g.balance = 20
    g.chip_index = 1                     # 25
    assert not g.can_afford() and not g.start_spin() and g.balance == 20
    g.balance = 5
    assert g.is_broke()


def test_history_and_cancel():
    g = Game()
    for n in range(20):
        g.start_spin()
        g.finish_spin(n % 37)
    assert len(g.history) == 16 and g.history[0] == 19
    g.start_spin()
    b = g.balance
    g.cancel_spin()
    assert g.balance == b + 10


def test_random_distribution():
    g = Game()
    seen = {g.draw_number() for _ in range(3000)}
    assert seen == set(range(37))


def test_bet_cells():
    g = Game()
    assert len(g.bet_cells()) == 18
    g.bet_index = 2
    assert g.bet_cells() == {0}


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("OK ", name)
