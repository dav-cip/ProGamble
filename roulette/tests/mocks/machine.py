"""Faux module 'machine' pour tester sur PC (pas pour l'ESP32)."""


class Pin:
    IN, OUT, PULL_UP, PULL_DOWN = 0, 1, 2, 3
    levels = {}      # id -> niveau force par les tests

    def __init__(self, pin_id, mode=-1, pull=-1, value=None):
        self.id = pin_id
        self.mode = mode
        if pin_id not in Pin.levels:
            Pin.levels[pin_id] = 1 if pull == Pin.PULL_UP else 0
        if value is not None:
            Pin.levels[pin_id] = value

    def value(self, v=None):
        if v is None:
            return Pin.levels[self.id]
        Pin.levels[self.id] = v


class ADC:
    ATTN_11DB = 3
    reading = 30000          # les tests changent cette valeur

    def __init__(self, pin):
        pass

    def atten(self, a):
        pass

    def read_u16(self):
        return ADC.reading


class PWM:
    def __init__(self, pin, freq=0, duty_u16=0):
        self.f, self.d = freq, duty_u16

    def freq(self, f=None):
        self.f = f

    def duty_u16(self, d=None):
        if d is not None:
            self.d = d


class SPI:
    present = True           # False = ecran debranche (lit 00 00 00 00)
    writes = 0
    read_baudrates = []      # vitesse du bus a chaque lecture (pour les tests)

    def __init__(self, *a, **k):
        self.baudrate = k.get("baudrate", 0)
        self.index = 0           # octet choisi par la commande 0xD9 (donnee 0x1N)

    def init(self, **k):
        self.baudrate = k.get("baudrate", self.baudrate)

    def write(self, data):
        SPI.writes += 1
        if len(data) == 1 and data[0] & 0xF0 == 0x10:
            self.index = data[0] & 0x0F

    def readinto(self, buf, write=0):
        SPI.read_baudrates.append(self.baudrate)
        if not SPI.present:
            buf[:] = b"\x00" * len(buf)          # ecran debranche
            return
        # Comme le vrai module (voir tft_diag.py) : la lecture directe de plusieurs
        # octets donne FF, seule la lecture d'un octet choisi par 0xD9 repond.
        # Et trop rapide pour lire (> ~6 MHz) -> reponse illisible.
        if len(buf) == 1 and self.baudrate <= 6_000_000:
            buf[0] = (0x00, 0x00, 0x93, 0x41)[min(self.index, 3)]
        else:
            buf[:] = b"\xff" * len(buf)

    def deinit(self):
        pass
