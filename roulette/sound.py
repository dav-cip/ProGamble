"""
sound.py - Buzzer passif commande en PWM, sans attente bloquante.

Une melodie est une suite de notes (frequence_Hz, duree_ms). Frequence 0 = silence.
Buzzer.play(melodie) la lance, puis Buzzer.update(now) la fait avancer a chaque tour
de la boucle principale. Le volume (rapport cyclique du PWM) suit la lumiere ambiante.
"""
from machine import Pin, PWM
from time import ticks_ms, ticks_diff, ticks_add

# ----- melodies -----
CLICK = ((2200, 12),)
TICK = ((1500, 15),)                                    # pendant la rotation
ERROR = ((220, 160), (0, 80), (220, 160))
BOOT = ((523, 90), (659, 90), (784, 120))
WIN = ((523, 120), (659, 120), (784, 120), (1047, 380))
LOSE = ((392, 220), (330, 220), (262, 450))
GAME_OVER = ((330, 250), (294, 250), (262, 250), (196, 600))


class Buzzer:
    def __init__(self, gpio):
        self.pwm = PWM(Pin(gpio), freq=1000, duty_u16=0)
        self.volume = 1.0          # 0.0 a 1.0
        self._seq = ()
        self._idx = 0
        self._until = 0
        self.playing = False

    def set_volume(self, volume):
        self.volume = max(0.15, min(1.0, volume))

    def _start_note(self, now):
        freq, ms = self._seq[self._idx]
        if freq > 0:
            self.pwm.freq(freq)
            self.pwm.duty_u16(int(32768 * self.volume))   # 50 % = le plus fort
        else:
            self.pwm.duty_u16(0)
        self._until = ticks_add(now, ms)

    def play(self, sequence):
        """Remplace le son en cours par une nouvelle melodie."""
        self._seq = sequence
        self._idx = 0
        self.playing = True
        self._start_note(ticks_ms())

    def stop(self):
        self.pwm.duty_u16(0)
        self.playing = False

    def update(self, now):
        if not self.playing or ticks_diff(now, self._until) < 0:
            return
        self._idx += 1
        if self._idx >= len(self._seq):
            self.stop()
        else:
            self._start_note(now)
