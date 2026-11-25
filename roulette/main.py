"""
main.py - Boucle principale du jeu ESP32 ROULETTE (machine a etats non bloquante).

ETATS :
  BOOT     demarrage (auto-test des sorties)
  SLEEP    veille : personne devant l'appareil depuis 60 s (ecran tamise)
  BET      choix du jeton et de la mise
  SPIN     la roue tourne (ecran + anneau + buzzer)
  RESULT   affichage du gain ou de la perte
  GAMEOVER plus assez de points pour jouer
  ERROR    ecran absent / probleme : mode sur, nouvelle tentative automatique

TRAJET DES DONNEES :
  photoresistance -> LightSensor (filtre, %) -> luminosite ecran (PWM) + anneau + volume
  PIR             -> PresenceSensor          -> veille / reveil
  boutons         -> ButtonPad (anti-rebond) -> evenements -> etat courant
Aucune attente bloquante : tout avance avec ticks_ms() / ticks_diff().
"""
import sys
import random
from time import ticks_ms, ticks_diff, ticks_add, sleep_ms

import config
import sound
import leds
from roulette import Game, color_of
from buttons import ButtonPad
from sensors import LightSensor, PresenceSensor
from leds import Ring, StatusLed
from sound import Buzzer
from errors import FaultManager, FAULT_LIGHT, FAULT_PIR, FAULT_SCREEN
from display import Backlight, create_screen

BOOT, SLEEP, BET, SPIN, RESULT, GAMEOVER, ERROR = range(7)


class App:
    def __init__(self):
        self.faults = FaultManager()
        self.game = Game()
        self.buzzer = Buzzer(config.PIN_BUZZER)
        self.ring = Ring(config.PIN_RING)
        self.led = StatusLed(config.PIN_STATUS_LED)
        self.pad = ButtonPad()
        self.light = LightSensor(config.PIN_LIGHT)
        self.pir = PresenceSensor(config.PIN_PIR)
        self.backlight = Backlight(config.PIN_TFT_BL)
        self.screen = None
        self.events = []
        self.active_row = "chip"          # "chip" ou "bet" : ce que PREV/NEXT modifient
        self.full_redraw = True
        self.shown_warning = ""
        self.last_activity = ticks_ms()
        self.next_env = 0
        self.next_retry = 0
        self.result = 0
        self.state = None
        self.state_start = 0
        self.next_tick = 0
        self.last_ball = -1
        self._try_init_screen()
        self.enter(BOOT if self.screen else ERROR)

    # ------------------------------------------------------------------
    # Ecran
    # ------------------------------------------------------------------
    def _try_init_screen(self):
        """Essaie d'initialiser l'ecran. Retourne True si ca a marche."""
        try:
            self.screen = create_screen()
            self.faults.update(FAULT_SCREEN, False)
            return True
        except Exception as e:                       # ecran absent, SPI en erreur...
            self.screen = None
            self.faults.update(FAULT_SCREEN, True)
            print("Ecran indisponible:", e)
            return False

    # ------------------------------------------------------------------
    # Changement d'etat (actions a l'entree de chaque etat)
    # ------------------------------------------------------------------
    def enter(self, state, now=None):
        now = ticks_ms() if now is None else now
        self.state = state
        self.state_start = now
        g, s = self.game, self.screen
        if state == BOOT:
            self.ring.set_mode(leds.BOOT, now)
            self.buzzer.play(sound.BOOT)
            self.backlight.set_percent(100)
            s.draw_splash()
        elif state == SLEEP:
            self.ring.set_mode(leds.IDLE, now)
            self.led.off()
            self.backlight.set_percent(config.BACKLIGHT_SLEEP_PCT)
            s.draw_sleep()
            self.full_redraw = True
        elif state == BET:
            self.ring.set_mode(leds.READY, now)
            self.led.off()
            self._apply_environment(now)
            if self.full_redraw:
                s.draw_all(g, self.active_row, self.light.percent, self._pir_text(),
                           self.faults.label())
                self.shown_warning = self.faults.label()
                self.full_redraw = False
            else:
                s.set_ball(None)
                s.draw_points(g.balance)
            s.draw_status("PRESS SPIN", "info")
        elif state == SPIN:
            self.result = g.draw_number()
            self.last_ball = -1
            self.next_tick = now
            self.ring.set_mode(leds.SPIN, now)
            self.led.blink(120)
            s.draw_points(g.balance)
            s.draw_status("SPINNING...", "spin")
        elif state == RESULT:
            won, net = g.finish_spin(self.result)
            s.set_ball(self.result)
            s.draw_last_result(self.result)
            s.draw_history(g.history)
            s.draw_points(g.balance)
            self.ring.set_mode(leds.RESULT, now, leds.RESULT_COLORS[color_of(self.result)], won)
            if won:
                s.draw_status("WIN +%d" % net, "win")
                self.buzzer.play(sound.WIN)
                self.led.on(3000, now)
            else:
                s.draw_status("LOSE %d" % net, "lose")
                self.buzzer.play(sound.LOSE)
                self.led.off()
        elif state == GAMEOVER:
            self.ring.set_mode(leds.ERROR, now)
            self.led.blink(1000)
            self.buzzer.play(sound.GAME_OVER)
            s.draw_status("GAME OVER-HOLD SPIN", "error")
        elif state == ERROR:
            self.ring.set_mode(leds.ERROR, now)
            self.led.blink(300)
            self.buzzer.play(sound.ERROR)
            self.next_retry = ticks_add(now, config.ERROR_RETRY_MS)
            self.full_redraw = True

    # ------------------------------------------------------------------
    # Lecture des entrees et de l'environnement
    # ------------------------------------------------------------------
    def _pir_text(self):
        if self.pir.warming_up:
            return "WAIT"
        if self.pir.stuck:
            return "BAD"
        return "ON" if self.pir.motion else "OFF"

    def _read_inputs(self, now):
        self.events = self.pad.poll(now)
        if self.events:
            self.last_activity = now
            self.pir.notify_activity(now)
        self.light.update(now)
        self.pir.update(now)
        if self.pir.usable and self.pir.motion:
            self.last_activity = now
        self.faults.update(FAULT_LIGHT, self.light.fault)
        self.faults.update(FAULT_PIR, self.pir.stuck)

    def _apply_environment(self, now):
        """La lumiere ambiante regle l'ecran (PWM), l'anneau et le volume du buzzer."""
        if self.light.fault or self.light.percent is None:
            pct = config.LIGHT_FALLBACK_PCT           # capteur en panne : valeur de secours
        else:
            pct = self.light.percent
        self.ring.set_brightness(0.3 + 0.7 * pct / 100)
        self.buzzer.set_volume(0.3 + 0.7 * pct / 100)
        if self.state not in (SLEEP, ERROR):
            low = config.BACKLIGHT_MIN_PCT
            self.backlight.set_percent(low + (100 - low) * pct / 100)

    def _update_environment(self, now):
        if ticks_diff(now, self.next_env) < 0:
            return
        self.next_env = ticks_add(now, config.ENV_UPDATE_MS)
        self._apply_environment(now)
        if self.state == BET and self.screen:
            self.screen.draw_env(None if self.light.fault else self.light.percent, self._pir_text())
            label = self.faults.label()
            if label != self.shown_warning:           # avertissement de panne dans le bandeau
                self.screen.draw_warning(label)
                self.shown_warning = label

    # ------------------------------------------------------------------
    # Un gestionnaire par etat
    # ------------------------------------------------------------------
    def _do_boot(self, now):
        if ticks_diff(now, self.state_start) >= config.BOOT_MS:
            self.enter(BET, now)

    def _do_sleep(self, now):
        if self.events or (self.pir.usable and self.pir.motion):
            # Le bouton qui reveille ne doit pas aussi jouer (ex: SPIN lancerait un tour)
            self.pad.mute_held()
            self.buzzer.play(sound.CLICK)
            self.enter(BET, now)                         # redessine l'ecran de jeu
            if self.game.is_broke():
                self.enter(GAMEOVER, now)                # on s'etait endormi en GAME OVER

    def _do_bet(self, now):
        g, s = self.game, self.screen
        for name, ev in self.events:
            if name in ("prev", "next") and ev in ("press", "repeat"):
                step = -1 if name == "prev" else 1
                if self.active_row == "chip":
                    g.change_chip(step)
                    s.draw_chips(g.chip_index, True)
                else:
                    g.change_bet(step)
                    s.draw_bet(g, True)
                    s.set_selection(g.bet_cells())
                if ev == "press":
                    self.buzzer.play(sound.CLICK)
            elif name == "select" and ev == "press":
                self.active_row = "bet" if self.active_row == "chip" else "chip"
                s.draw_chips(g.chip_index, self.active_row == "chip")
                s.draw_bet(g, self.active_row == "bet")
                self.buzzer.play(sound.CLICK)
            elif name == "spin" and ev == "click":
                if g.start_spin():
                    self.enter(SPIN, now)
                    return
                s.draw_status("NOT ENOUGH POINTS", "warn")      # mise > solde : refusee
                self.buzzer.play(sound.ERROR)
            elif name == "spin" and ev == "long":
                g.reset()                                        # reinitialisation locale
                self.full_redraw = True
                self.enter(BET, now)
                s.draw_status("NEW GAME", "info")
                self.buzzer.play(sound.BOOT)
                return
        if ticks_diff(now, self.last_activity) >= config.SLEEP_TIMEOUT_MS:
            self.enter(SLEEP, now)

    def _do_spin(self, now):
        if ticks_diff(now, self.next_tick) < 0:
            return
        elapsed = ticks_diff(now, self.state_start)
        if elapsed >= config.SPIN_TOTAL_MS:
            self.ring.spin_step()
            self.screen.set_ball(self.result)
            self.enter(RESULT, now)
            return
        # La bille ralentit : l'intervalle grandit comme le carre du temps ecoule
        ratio = elapsed / config.SPIN_TOTAL_MS
        interval = config.SPIN_MIN_INTERVAL_MS + int(
            (config.SPIN_MAX_INTERVAL_MS - config.SPIN_MIN_INTERVAL_MS) * ratio * ratio)
        # Numero d'animation (different du precedent, sans rapport avec le resultat final)
        ball = (self.last_ball + 1 + random.randrange(36)) % 37
        self.last_ball = ball
        self.screen.set_ball(ball)
        self.ring.spin_step()
        self.buzzer.play(sound.TICK)
        self.next_tick = ticks_add(now, interval)

    def _do_result(self, now):
        clicked = any(ev == "click" for _, ev in self.events)
        if clicked or ticks_diff(now, self.state_start) >= config.RESULT_SHOW_MS:
            if self.game.is_broke():
                self.enter(GAMEOVER, now)
            else:
                self.enter(BET, now)

    def _do_gameover(self, now):
        for name, ev in self.events:
            if name == "spin" and ev == "long":
                self.game.reset()
                self.full_redraw = True
                self.enter(BET, now)
                self.screen.draw_status("NEW GAME", "info")
                return
        if ticks_diff(now, self.last_activity) >= config.SLEEP_TIMEOUT_MS:
            self.enter(SLEEP, now)                       # personne : veille, comme en BET

    def _do_error(self, now):
        """Ecran absent : on signale (anneau rouge, DEL, bips) et on reessaie."""
        retry_now = any(n == "spin" and ev == "click" for n, ev in self.events)
        if retry_now or ticks_diff(now, self.next_retry) >= 0:
            if self._try_init_screen():
                self.enter(BOOT, now)
            else:
                self.next_retry = ticks_add(now, config.ERROR_RETRY_MS)
                self.buzzer.play(sound.ERROR)

    # ------------------------------------------------------------------
    # Boucle
    # ------------------------------------------------------------------
    def step(self):
        """Un tour de boucle : lire, decider, mettre a jour les sorties."""
        now = ticks_ms()
        self._read_inputs(now)
        self._update_environment(now)
        handlers = (self._do_boot, self._do_sleep, self._do_bet, self._do_spin,
                    self._do_result, self._do_gameover, self._do_error)
        handlers[self.state](now)
        self.buzzer.update(now)
        self.ring.update(now)
        self.led.update(now)

    def recover(self, error):
        """Erreur imprevue : on rembourse la mise et on passe en mode sur (ERROR)."""
        try:
            sys.print_exception(error)
        except AttributeError:
            print("Erreur:", error)
        if self.state == SPIN:
            self.game.cancel_spin()
        self.screen = None
        self.faults.update(FAULT_SCREEN, True)
        self.enter(ERROR)

    def safe_step(self):
        """Un tour de boucle protege : une erreur imprevue ne plante pas le jeu."""
        try:
            self.step()
        except Exception as e:                          # Ctrl-C reste possible (pas une Exception)
            self.recover(e)

    def run(self):
        while True:
            self.safe_step()
            sleep_ms(5)                                  # petit repos : pas une attente de tache


def main():
    App().run()


if __name__ == "__main__":
    main()
