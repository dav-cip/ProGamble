"""
buttons.py - Lecture des 4 boutons avec anti-rebond, sans aucune attente bloquante.

Chaque bouton est branche entre la broche et GND (resistance PULL_UP interne :
la broche vaut 1 au repos et 0 quand on appuie).

Evenements produits par Button.update() :
  "press"   : appui confirme (apres anti-rebond)
  "release" : relachement
  "click"   : relachement d'un appui COURT (pas un appui long)
  "long"    : bouton maintenu plus de LONG_PRESS_MS (une seule fois)
  "repeat"  : repetition automatique tant que le bouton est maintenu
"""
from machine import Pin
from time import ticks_ms, ticks_diff, ticks_add
import config


class Button:
    def __init__(self, gpio):
        self.pin = Pin(gpio, Pin.IN, Pin.PULL_UP)
        self.raw = False           # etat lu a l'instant (True = appuye)
        self.stable = False        # etat confirme apres anti-rebond
        self.changed_at = ticks_ms()
        self.pressed_at = 0
        self.long_sent = False
        self.next_repeat = 0
        self.muted = False         # True = on ignore cet appui jusqu'au relachement

    def mute(self):
        """Ignore l'appui en cours (pas de click, long ni repeat) jusqu'au relachement."""
        if self.stable:
            self.muted = True

    def update(self, now):
        events = []
        raw = self.pin.value() == 0
        if raw != self.raw:                       # l'etat vient de bouger : on repart le chrono
            self.raw = raw
            self.changed_at = now
        if raw != self.stable and ticks_diff(now, self.changed_at) >= config.DEBOUNCE_MS:
            self.stable = raw                     # stable assez longtemps : on l'accepte
            if raw:
                self.pressed_at = now
                self.long_sent = False
                self.next_repeat = ticks_add(now, config.REPEAT_DELAY_MS)
                events.append("press")
            else:
                events.append("release")
                if not self.long_sent and not self.muted:
                    events.append("click")
                self.muted = False
        elif self.stable and not self.muted:      # bouton maintenu
            if not self.long_sent and ticks_diff(now, self.pressed_at) >= config.LONG_PRESS_MS:
                self.long_sent = True
                events.append("long")
            if ticks_diff(now, self.next_repeat) >= 0:
                self.next_repeat = ticks_add(now, config.REPEAT_MS)
                events.append("repeat")
        return events


class ButtonPad:
    """Regroupe les 4 boutons : poll() retourne une liste de (nom, evenement)."""

    def __init__(self):
        self.buttons = {
            "prev": Button(config.PIN_BTN_PREV),
            "next": Button(config.PIN_BTN_NEXT),
            "select": Button(config.PIN_BTN_SELECT),
            "spin": Button(config.PIN_BTN_SPIN),
        }

    def poll(self, now):
        out = []
        for name, button in self.buttons.items():
            for ev in button.update(now):
                out.append((name, ev))
        return out

    def mute_held(self):
        """Les boutons encore enfonces ne produiront plus rien avant d'etre relaches."""
        for button in self.buttons.values():
            button.mute()
