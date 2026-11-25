"""
Test de fumee : fait tourner main.py sur PC avec un faux materiel (tests/mocks)
et une fausse horloge. Il verifie les etats, les pannes et la reprise.
Lancer :  python3 tests/test_smoke.py
"""
import sys, os, time
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "mocks"))
sys.path.insert(0, os.path.join(HERE, ".."))

# ----- fausse horloge MicroPython -----
CLOCK = [1000]
time.ticks_ms = lambda: CLOCK[0]
time.ticks_diff = lambda a, b: a - b
time.ticks_add = lambda a, b: a + b
def _sleep_ms(ms):
    CLOCK[0] += ms
time.sleep_ms = _sleep_ms

import config
import machine
import main as M

Pin, ADC, SPI = machine.Pin, machine.ADC, machine.SPI


def run(app, ms):
    end = CLOCK[0] + ms
    while CLOCK[0] < end:
        app.safe_step()
        CLOCK[0] += 5


def press(app, name, hold=100):
    gpio = {"prev": config.PIN_BTN_PREV, "next": config.PIN_BTN_NEXT,
            "select": config.PIN_BTN_SELECT, "spin": config.PIN_BTN_SPIN}[name]
    Pin.levels[gpio] = 0
    run(app, hold)
    Pin.levels[gpio] = 1
    run(app, 100)


def fresh():
    ADC.reading = 30000
    SPI.present = True
    Pin.levels.clear()
    return M.App()


def test_boot_and_spin():
    app = fresh()
    assert app.state == M.BOOT
    run(app, 2000)
    assert app.state == M.BET
    press(app, "spin")
    assert app.state == M.SPIN and app.game.balance == 490
    run(app, config.SPIN_TOTAL_MS + 300)
    assert app.state == M.RESULT and len(app.game.history) == 1
    run(app, config.RESULT_SHOW_MS + 300)
    assert app.state == M.BET


def test_menu_navigation():
    app = fresh()
    run(app, 2000)
    press(app, "next")
    assert app.game.chip == 25
    press(app, "select")
    assert app.active_row == "bet"
    press(app, "next")
    assert app.game.bet_name() == "BLACK"
    press(app, "prev", hold=1500)        # maintenu : repetition automatique
    assert app.game.bet_index != 1


def test_cannot_overbet():
    app = fresh()
    run(app, 2000)
    app.game.balance = 5
    press(app, "spin")
    assert app.state == M.BET and app.game.balance == 5


def test_light_fault_and_recovery():
    app = fresh()
    run(app, 2000)
    ADC.reading = 0
    run(app, config.LIGHT_FAULT_MS + 500)
    assert app.faults.has("LIGHT")
    ADC.reading = 30000
    run(app, config.LIGHT_RECOVER_MS + 800)
    assert not app.faults.has("LIGHT")


def test_screen_absent_then_recovers():
    SPI.present = False
    Pin.levels.clear()
    app = M.App()
    assert app.state == M.ERROR and app.faults.has("SCREEN")
    SPI.present = True
    run(app, config.ERROR_RETRY_MS + 500)
    assert app.state in (M.BOOT, M.BET) and not app.faults.has("SCREEN")
    run(app, 2500)
    assert app.state == M.BET


def test_screen_id_read_slow_then_full_speed():
    SPI.read_baudrates.clear()
    app = fresh()
    assert app.state == M.BOOT                 # l'ecran a bien ete reconnu
    assert SPI.read_baudrates and max(SPI.read_baudrates) <= 6_000_000
    assert app.screen.tft.spi.baudrate == config.TFT_BAUDRATE


def test_sleep_and_wake():
    app = fresh()
    run(app, config.PIR_WARMUP_MS + 1000)      # le PIR est pret
    assert app.state in (M.BET, M.SLEEP)
    run(app, config.SLEEP_TIMEOUT_MS + 2000)
    assert app.state == M.SLEEP
    Pin.levels[config.PIN_PIR] = 1             # quelqu'un s'approche
    run(app, 300)
    assert app.state == M.BET


def test_wake_with_spin_does_not_bet():
    app = fresh()
    run(app, 2000 + config.SLEEP_TIMEOUT_MS + 1000)
    assert app.state == M.SLEEP
    press(app, "spin")                         # ce bouton sert seulement a reveiller
    assert app.state == M.BET and app.game.balance == config.START_BALANCE
    press(app, "spin")                         # le prochain appui lance bien le tour
    assert app.state == M.SPIN


def test_exception_recovery_refunds():
    app = fresh()
    run(app, 2000)
    press(app, "spin")
    assert app.state == M.SPIN
    app.screen.set_ball = lambda n: 1 / 0      # on simule une panne en plein tour
    run(app, 1000)
    assert app.state == M.ERROR and app.game.balance == 500
    run(app, config.ERROR_RETRY_MS + 3000)
    assert app.state == M.BET


def test_game_over_and_new_game():
    app = fresh()
    run(app, 2000)
    app.game.balance = 10
    app.game.draw_number = lambda: 0           # le zero fait perdre le ROUGE
    press(app, "spin")
    run(app, config.SPIN_TOTAL_MS + config.RESULT_SHOW_MS + 500)
    assert app.state == M.GAMEOVER and app.game.balance == 0
    press(app, "spin", hold=config.LONG_PRESS_MS + 200)
    assert app.state == M.BET and app.game.balance == config.START_BALANCE


def test_game_over_sleeps_and_wakes_to_game_over():
    app = fresh()
    run(app, 2000)
    app.game.balance = 10
    app.game.draw_number = lambda: 0
    press(app, "spin")
    run(app, config.SPIN_TOTAL_MS + config.RESULT_SHOW_MS + 500)
    assert app.state == M.GAMEOVER
    run(app, config.SLEEP_TIMEOUT_MS)
    assert app.state == M.SLEEP
    press(app, "next")                         # reveil : on retrouve l'ecran GAME OVER
    assert app.state == M.GAMEOVER
    press(app, "spin", hold=config.LONG_PRESS_MS + 200)
    assert app.state == M.BET and app.game.balance == config.START_BALANCE


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("OK ", name)
