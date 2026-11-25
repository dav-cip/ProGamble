"""
leds.py - Anneau WS2812B (RING_COUNT DEL, 24 sur notre anneau) et DEL d'etat, animations non bloquantes.

Anneau : on choisit un MODE avec set_mode(), puis update(now) dessine les images
au bon rythme. L'intensite globale suit la lumiere ambiante et ne depasse jamais
RING_MAX_LEVEL (pour limiter le courant tire sur le 5 V).
"""
from machine import Pin
import neopixel
from time import ticks_diff, ticks_add
import config

# Modes de l'anneau
OFF, BOOT, IDLE, READY, SPIN, RESULT, ERROR = range(7)

GOLD = (255, 170, 0)
RESULT_COLORS = {"red": (255, 0, 0), "black": (255, 255, 255), "green": (0, 255, 0)}
_BOOT_COLORS = ((255, 0, 0), (0, 255, 0), (0, 0, 255))
_COMET = (1.0, 0.55, 0.3, 0.12)      # luminosite de la tete et de la queue


class Ring:
    def __init__(self, gpio):
        self.np = neopixel.NeoPixel(Pin(gpio, Pin.OUT), config.RING_COUNT)
        self.n = config.RING_COUNT
        self.brightness = 1.0
        self.mode = OFF
        self.color = GOLD
        self.won = False
        self.head = 0              # position de la tete de la comete
        self._idx = 0
        self._start = 0
        self._next = 0
        self._dirty = True

    def _scaled(self, color, k=1.0):
        f = config.RING_MAX_LEVEL * self.brightness * k
        return (int(color[0] * f), int(color[1] * f), int(color[2] * f))

    def _fill(self, color):
        for i in range(self.n):
            self.np[i] = color

    def _comet(self, color):
        self._fill((0, 0, 0))
        for i, k in enumerate(_COMET):
            self.np[(self.head - i) % self.n] = self._scaled(color, k)

    def set_brightness(self, value):
        value = max(0.1, min(1.0, value))
        if abs(value - self.brightness) > 0.02:
            self.brightness = value
            self._dirty = True

    def set_mode(self, mode, now, color=None, won=False):
        self.mode = mode
        self.color = color if color else GOLD
        self.won = won
        self._start = now
        self._next = now
        self._idx = 0
        self._dirty = True

    def spin_step(self):
        """Avance la comete d'une case (appele a chaque tick de la roulette)."""
        self.head = (self.head + 1) % self.n
        self._dirty = True

    def update(self, now):
        if not self._dirty and ticks_diff(now, self._next) < 0:
            return
        mode = self.mode
        interval = 100
        if mode == OFF:
            self._fill((0, 0, 0))
            interval = 1000
        elif mode == BOOT:
            self._fill(self._scaled(_BOOT_COLORS[self._idx % 3]))
            self._idx += 1
            interval = 200
        elif mode == IDLE:                               # veille : un point dore lent
            self._fill((0, 0, 0))
            self.np[self._idx % self.n] = self._scaled(GOLD, 0.5)
            self._idx += 1
            interval = 300
        elif mode == READY:                              # mise : deux points opposes
            self._fill((0, 0, 0))
            self.np[self._idx % self.n] = self._scaled(GOLD, 0.5)
            self.np[(self._idx + self.n // 2) % self.n] = self._scaled(GOLD, 0.5)
            self._idx += 1
            interval = 150
        elif mode == SPIN:                               # comete pilotee par spin_step()
            self._comet(GOLD)
            interval = 1000
        elif mode == RESULT:
            elapsed = ticks_diff(now, self._start)
            if elapsed < 700:                            # la comete s'arrete sur la case finale
                self._comet(self.color)
            elif self.won and elapsed < 3000:            # gain : clignote
                on = (elapsed // 200) % 2 == 0
                self._fill(self._scaled(self.color) if on else (0, 0, 0))
            else:                                        # couleur fixe du resultat
                self._fill(self._scaled(self.color, 1.0 if self.won else 0.6))
            interval = 100
        elif mode == ERROR:                              # rouge qui clignote
            on = self._idx % 2 == 0
            self._fill(self._scaled((255, 0, 0)) if on else (0, 0, 0))
            self._idx += 1
            interval = 400
        self.np.write()
        self._dirty = False
        self._next = ticks_add(now, interval)


class StatusLed:
    """DEL d'etat : sortie NUMERIQUE tout ou rien (allumee, eteinte ou clignotante)."""

    def __init__(self, gpio):
        self.pin = Pin(gpio, Pin.OUT, value=0)
        self._period = 0           # 0 = pas de clignotement
        self._until = None         # fin d'un allumage temporaire
        self._next = 0
        self._state = 0

    def off(self):
        self._period = 0
        self._until = None
        self._set(0)

    def on(self, duration_ms=None, now=None):
        """Allume (pour 'duration_ms' ms si precise, avec 'now')."""
        self._period = 0
        self._until = ticks_add(now, duration_ms) if duration_ms else None
        self._set(1)

    def blink(self, period_ms):
        self._period = period_ms
        self._until = None

    def _set(self, value):
        self._state = value
        self.pin.value(value)

    def update(self, now):
        if self._until is not None and ticks_diff(now, self._until) >= 0:
            self.off()
        elif self._period and ticks_diff(now, self._next) >= 0:
            self._set(1 - self._state)
            self._next = ticks_add(now, self._period // 2)
