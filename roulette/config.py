"""
config.py - Toute la configuration du projet au meme endroit.

Si tu changes un branchement ou un reglage, tu ne modifies QUE ce fichier.
Carte : Arduino Nano ESP32 (ABX00083), MicroPython.
"""

# ---------------------------------------------------------------
# 1. BROCHES  (noms Arduino -> numeros GPIO de l'ESP32-S3)
# ---------------------------------------------------------------
# Correspondance de la carte Nano ESP32. A VERIFIER sur la fiche de
# brochage officielle (docs.arduino.cc/hardware/nano-esp32).
# On travaille avec les numeros GPIO : ca marche meme si le firmware
# ne connait pas les noms "D2", "A0", etc.
_PINMAP = {
    "D2": 5, "D3": 6, "D4": 7, "D5": 8, "D6": 9, "D7": 10,
    "D8": 17, "D9": 18, "D10": 21, "D11": 38, "D12": 47, "D13": 48,
    "A0": 1, "A1": 2, "A2": 3, "A3": 4,
}


def pin(name):
    """Retourne le numero GPIO a partir du nom Arduino (ex: 'D2' -> 5)."""
    return _PINMAP[name]


# Ecran TFT ILI9341 (SPI materiel)
PIN_TFT_SCK = pin("D13")
PIN_TFT_MOSI = pin("D11")   # pin SDI / MOSI de l'ecran
PIN_TFT_MISO = pin("D12")   # pin SDO / MISO (sert au test de presence)
PIN_TFT_CS = pin("D10")
PIN_TFT_DC = pin("D9")
PIN_TFT_RST = pin("D8")
# Retro-eclairage : None = la pin LED de l'ecran est branchee sur 3V3 (toujours allume).
# Pour le varier en PWM : brancher LED sur D6 (seulement si le module a un transistor
# de retro-eclairage) et mettre pin("D6").
PIN_TFT_BL = None

# Boutons (un cote sur la broche, l'autre cote sur GND)
PIN_BTN_PREV = pin("D2")
PIN_BTN_NEXT = pin("D3")
PIN_BTN_SELECT = pin("D4")
PIN_BTN_SPIN = pin("D5")

# Sorties
PIN_RING = pin("D7")          # anneau WS2812B (DIN)
PIN_BUZZER = pin("A3")        # buzzer passif (PWM)
PIN_STATUS_LED = pin("A2")    # DEL d'etat (marche/arret)

# Capteurs
PIN_LIGHT = pin("A0")         # photoresistance (ANALOGIQUE)
PIN_PIR = pin("A1")           # capteur de presence PIR (NUMERIQUE)

# ---------------------------------------------------------------
# 2. ECRAN
# ---------------------------------------------------------------
TFT_BAUDRATE = 40_000_000     # baisser a 20_000_000 si l'image est instable
# Vitesse pendant l'init et la lecture de l'ID : l'ILI9341 ne sait pas LIRE plus
# vite que ~6 MHz (fiche technique). On passe a TFT_BAUDRATE une fois l'ecran pret.
TFT_INIT_BAUDRATE = 4_000_000
# Registre MADCTL : 0x28 = paysage. Essaie 0xE8 si l'image est a l'envers,
# ou 0x20 si les couleurs rouge/bleu sont inversees.
TFT_MADCTL = 0x28
TFT_CHECK_ID = True           # True = test de presence de l'ecran (fil MISO requis)

# ---------------------------------------------------------------
# 3. JEU
# ---------------------------------------------------------------
START_BALANCE = 500
CHIPS = (10, 25, 50, 100)
HISTORY_SIZE = 16             # nombre de tirages gardes et affiches

# ---------------------------------------------------------------
# 4. BOUTONS (temps en ms)
# ---------------------------------------------------------------
DEBOUNCE_MS = 25
LONG_PRESS_MS = 1500
REPEAT_DELAY_MS = 450         # delai avant la repetition d'un bouton maintenu
REPEAT_MS = 90

# ---------------------------------------------------------------
# 5. CAPTEUR DE LUMIERE (analogique) - A CALIBRER avec calibrate.py
# ---------------------------------------------------------------
LIGHT_RAW_DARK = 4000         # lecture (0-65535) dans le noir
LIGHT_RAW_BRIGHT = 50000      # lecture sous une forte lumiere
LIGHT_SAMPLE_MS = 100
LIGHT_OVERSAMPLE = 8          # moyenne de 8 lectures a chaque echantillon
LIGHT_FILTER_ALPHA = 0.15     # filtre exponentiel (0 = tres lent, 1 = pas de filtre)
LIGHT_FAULT_LOW = 50          # lecture <= : capteur en court-circuit / debranche
LIGHT_FAULT_HIGH = 65400      # lecture >= : idem (cote 3,3 V)
LIGHT_FAULT_MS = 3000         # duree avant de declarer la panne
LIGHT_RECOVER_MS = 1000       # duree de lecture valide pour effacer la panne
LIGHT_FALLBACK_PCT = 70       # luminosite utilisee si le capteur est en panne

# ---------------------------------------------------------------
# 6. CAPTEUR DE PRESENCE PIR (numerique)
# ---------------------------------------------------------------
PIR_WARMUP_MS = 30_000        # le HC-SR501 a besoin d'environ 30 s apres le demarrage
PIR_STUCK_MS = 600_000        # signal haut 10 min sans aucune action = bloque
SLEEP_TIMEOUT_MS = 60_000     # sans presence ni bouton pendant 60 s -> veille

# ---------------------------------------------------------------
# 7. LUMINOSITE / VOLUME (relies au capteur de lumiere)
# ---------------------------------------------------------------
BACKLIGHT_MIN_PCT = 20        # luminosite mini de l'ecran dans le noir
BACKLIGHT_SLEEP_PCT = 8       # luminosite en veille
RING_MAX_LEVEL = 0.35         # plafond de l'anneau (limite le courant)
ENV_UPDATE_MS = 300           # periode de mise a jour de la luminosite

# ---------------------------------------------------------------
# 8. ANIMATION DE LA ROULETTE
# ---------------------------------------------------------------
RING_COUNT = 24               # nombre de DEL de l'anneau (le notre en a 24)
SPIN_TOTAL_MS = 4500
SPIN_MIN_INTERVAL_MS = 60     # vitesse au debut
SPIN_MAX_INTERVAL_MS = 400    # vitesse a la fin (ralentit)
RESULT_SHOW_MS = 4000
BOOT_MS = 1800
ERROR_RETRY_MS = 5000         # nouvelle tentative d'init de l'ecran
