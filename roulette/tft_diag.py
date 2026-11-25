"""
tft_diag.py - Diagnostic de l'ecran (a lancer a la main depuis Thonny, comme calibrate.py).

Il repond a deux questions :
  1. L'ecran repond-il quand on lui demande son identifiant ? (fil SDO/MISO -> D12)
  2. L'ecran affiche-t-il des couleurs ? (fils SCK, SDI/MOSI, CS, DC, RESET, VCC, GND)

Arreter main.py (Stop / Ctrl-C), lancer ce fichier, regarder l'ecran et lire la
conclusion affichee a la fin.
"""
from machine import Pin, SPI
import time
import config
from ili9341 import ILI9341, color565

READ_BAUD = 1_000_000           # tres lent : la lecture marche meme avec de longs fils


def hexs(data):
    return " ".join("%02X" % b for b in data)


def read_direct(tft, cmd, n):
    """Envoie la commande puis lit n octets (meme methode que ili9341.read_id)."""
    buf = bytearray(n)
    tft.cs.value(0)
    tft.dc.value(0)
    tft.spi.write(bytes((cmd,)))
    tft.dc.value(1)
    tft.spi.readinto(buf)
    tft.cs.value(1)
    return bytes(buf)


def read_indexed(tft, cmd, index):
    """Methode d'Adafruit / TFT_eSPI : 0xD9 choisit l'octet a lire, puis on en lit un."""
    tft._cmd(0xD9, bytes((0x10 + index,)))
    return read_direct(tft, cmd, 1)[0]


print("=== Diagnostic ecran ===")
# Retroeclairage allume, que la broche LED soit sur 3V3 ou sur D6
Pin(config.PIN_TFT_BL if config.PIN_TFT_BL is not None else config.pin("D6"), Pin.OUT, value=1)
spi = SPI(1, baudrate=READ_BAUD, polarity=0, phase=0, sck=Pin(config.PIN_TFT_SCK),
          mosi=Pin(config.PIN_TFT_MOSI), miso=Pin(config.PIN_TFT_MISO))
tft = ILI9341(spi, Pin(config.PIN_TFT_CS, Pin.OUT, value=1), Pin(config.PIN_TFT_DC, Pin.OUT),
              Pin(config.PIN_TFT_RST, Pin.OUT), madctl=config.TFT_MADCTL, check_id=False)
print("Ecran initialise SANS test d'identifiant.")

# ----- 1. lectures sur MISO -----
reads = [
    ("ID D3, lecture directe  ", read_direct(tft, 0xD3, 4)),
    ("ID D3, methode Adafruit ", bytes(read_indexed(tft, 0xD3, i) for i in (1, 2, 3))),
    ("ID 04 (RDDID)           ", read_direct(tft, 0x04, 4)),
    ("Etat 0A (power mode)    ", read_direct(tft, 0x0A, 1)),
]
print()
for name, data in reads:
    print(name, ":", hexs(data))
everything = b"".join(d for _, d in reads)
all_ff = all(b == 0xFF for b in everything)
all_00 = all(b == 0x00 for b in everything)

# ----- 2. couleurs (regarder l'ecran !) -----
print()
print("Regarde l'ecran : ROUGE, VERT, BLEU, BLANC, puis 'DIAGNOSTIC'.")
tests = (("ROUGE", (255, 0, 0)), ("VERT", (0, 255, 0)), ("BLEU", (0, 0, 255)),
         ("BLANC", (255, 255, 255)))
black = color565(0, 0, 0)
for name, rgb in tests:
    col = color565(*rgb)
    tft.fill_screen(col)
    tft.text(name, 160 - len(name) * 12, 108, black if name == "BLANC" else color565(255, 255, 255),
             col, 3)
    print("  l'ecran devrait etre", name)
    time.sleep_ms(1500)
tft.fill_screen(black)
tft.text("DIAGNOSTIC", 80, 100, color565(255, 205, 0), black, 2)
tft.text("voir la console", 100, 130, color565(200, 200, 200), black, 1)

# ----- 3. conclusion -----
print()
print("=== Conclusion ===")
if all_ff or all_00:
    print("MISO : AUCUNE reponse (que des %s)." % ("FF" if all_ff else "00"))
    print("  - Verifier le fil : broche SDO (MISO) de l'ecran -> D12.")
    print("    Attention a ne pas prendre T_DO (broche tactile juste a cote).")
    print("  - Verifier que le fil est bien enfonce des deux cotes (essayer un autre fil).")
    print("  - Si l'ecran n'a PAS de broche SDO/MISO : mettre TFT_CHECK_ID = False dans config.py.")
else:
    print("MISO : l'ecran repond. Le fil SDO -> D12 fonctionne.")
    if b"\x93\x41" in everything:
        print("  Controleur ILI9341 reconnu (93 41).")
    elif b"\x94\x88" in everything:
        print("  C'est un ILI9488 (94 88), pas un ILI9341 : il faut un autre pilote.")
    elif b"\x77\x96" in everything:
        print("  C'est un ST7796 (77 96), pas un ILI9341 : il faut un autre pilote.")
    elif b"\x85\x85" in everything or b"\x85\x52" in everything:
        print("  Ca ressemble a un ST7789, pas a un ILI9341 : le pilote ne convient pas.")
    else:
        print("  Identifiant inattendu : envoyer ces valeurs a l'equipe.")
print("Couleurs :")
print("  - Vu ROUGE, VERT, BLEU, BLANC : l'ecran et les fils SCK/SDI/CS/DC/RESET sont bons.")
print("  - Couleurs inversees (ex. rouge -> cyan) : le controleur n'est peut-etre pas un ILI9341.")
print("  - Image brouillee, rayee ou seulement une partie de l'ecran : probablement un ILI9488")
print("    (ecran 480x320, couleurs sur 3 octets) -> il faut un autre pilote.")
print("  - Ecran reste blanc : verifier SCK->D13, SDI->D11, CS->D10, DC->D9, RESET->D8.")
print("  - Ecran noir : verifier VCC, GND et la broche LED (retroeclairage).")
