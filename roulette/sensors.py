"""
sensors.py - Les deux capteurs du projet.

  LightSensor    : photoresistance, entree ANALOGIQUE (ADC)  -> lumiere ambiante en %
  PresenceSensor : capteur PIR, entree NUMERIQUE             -> presence / mouvement

Les deux classes se mettent a jour avec update(now), sans jamais attendre.
"""
from machine import Pin, ADC
from time import ticks_ms, ticks_diff, ticks_add
import config


class LightSensor:
    def __init__(self, gpio, dark_raw=None, bright_raw=None):
        self.adc = ADC(Pin(gpio))
        self.adc.atten(ADC.ATTN_11DB)          # plage de mesure ~0 a 3,3 V
        self.dark = config.LIGHT_RAW_DARK if dark_raw is None else dark_raw
        self.bright = config.LIGHT_RAW_BRIGHT if bright_raw is None else bright_raw
        self.raw = None            # derniere lecture brute (0-65535)
        self.filtered = None       # lecture lissee
        self.percent = None        # 0 (noir) a 100 (tres lumineux)
        self.fault = False
        self._next_sample = ticks_ms()
        self._bad_since = None
        self._good_since = None

    def read_raw(self):
        """Moyenne de plusieurs lectures pour reduire le bruit de l'ADC."""
        total = 0
        for _ in range(config.LIGHT_OVERSAMPLE):
            total += self.adc.read_u16()
        return total // config.LIGHT_OVERSAMPLE

    def update(self, now):
        if ticks_diff(now, self._next_sample) < 0:
            return
        self._next_sample = ticks_add(now, config.LIGHT_SAMPLE_MS)
        try:
            raw = self.read_raw()
        except (OSError, ValueError):
            raw = None
        self.raw = raw

        # --- validation : valeur hors plage = capteur en court-circuit ou debranche ---
        bad = raw is None or raw <= config.LIGHT_FAULT_LOW or raw >= config.LIGHT_FAULT_HIGH
        if bad:
            self._good_since = None
            if self._bad_since is None:
                self._bad_since = now
            elif ticks_diff(now, self._bad_since) >= config.LIGHT_FAULT_MS:
                self.fault = True
            return                                   # on ne filtre pas une mauvaise valeur
        self._bad_since = None
        if self._good_since is None:
            self._good_since = now
        elif self.fault and ticks_diff(now, self._good_since) >= config.LIGHT_RECOVER_MS:
            self.fault = False                       # la panne disparait toute seule

        # --- filtre exponentiel puis conversion en pourcentage (calibration) ---
        if self.filtered is None:
            self.filtered = raw
        else:
            self.filtered += (raw - self.filtered) * config.LIGHT_FILTER_ALPHA
        span = self.bright - self.dark               # fonctionne meme si le capteur est "inverse"
        pct = (self.filtered - self.dark) * 100 / span
        self.percent = max(0, min(100, int(pct)))


class PresenceSensor:
    def __init__(self, gpio):
        self.pin = Pin(gpio, Pin.IN, Pin.PULL_DOWN)   # debranche -> lit 0 (pas de bruit)
        self._t0 = ticks_ms()
        self.warming_up = True     # le PIR donne n'importe quoi les ~30 premieres secondes
        self.motion = False        # mouvement detecte en ce moment
        self.stuck = False         # signal bloque a 1 trop longtemps
        self._high_since = None

    @property
    def usable(self):
        """Vrai si on peut se fier au capteur."""
        return (not self.warming_up) and (not self.stuck)

    def update(self, now):
        if self.warming_up:
            if ticks_diff(now, self._t0) < config.PIR_WARMUP_MS:
                self.motion = False
                return
            self.warming_up = False
        level = self.pin.value() == 1
        self.motion = level
        if level:
            if self._high_since is None:
                self._high_since = now
            elif ticks_diff(now, self._high_since) >= config.PIR_STUCK_MS:
                self.stuck = True
        else:
            self._high_since = None
            self.stuck = False                         # se corrige quand le signal retombe

    def notify_activity(self, now):
        """Un bouton a ete presse : quelqu'un est la, donc le signal haut est normal."""
        if self._high_since is not None:
            self._high_since = now
        self.stuck = False
