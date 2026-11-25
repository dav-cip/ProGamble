"""
display.py - Interface du jeu sur l'ecran 320 x 240 (paysage).

Disposition (en pixels, y = ligne du haut) :
    0-15   bandeau titre  (+ avertissement a droite en cas de panne)
   20-36   POINTS (solde) a gauche, lumiere et PIR a droite
   40-59   rangee des JETONS (10 / 25 / 50 / 100)
   63-81   rangee de la MISE choisie
   86-151  grille de la roulette : 0 + 36 numeros (rouge / noir / vert)
  158-212  dernier tirage (gauche) et historique (droite)
  216-239  barre de message : SPINNING / WIN / LOSE ...
On ne redessine que la zone qui change (rapide, pas de scintillement).
"""
from machine import Pin, SPI, PWM
import config
from ili9341 import ILI9341, color565
from roulette import color_of

# ----- couleurs -----
C_FELT = color565(0, 70, 36)        # tapis vert fonce
C_GOLD = color565(255, 205, 0)
C_HEADER = color565(212, 175, 55)
C_WHITE = color565(255, 255, 255)
C_BLACK = color565(15, 15, 15)
C_RED = color565(200, 25, 25)
C_GREEN = color565(0, 140, 70)
C_GREY = color565(170, 170, 170)
C_PANEL = color565(0, 45, 24)
C_BLUE = color565(30, 70, 200)
C_ORANGE = color565(255, 140, 0)

_CELL_COLORS = {"red": C_RED, "black": C_BLACK, "green": C_GREEN}

# Jetons : (couleur du jeton, couleur du texte)
_CHIP_STYLE = (
    (color565(190, 190, 190), C_BLACK),
    (C_RED, C_WHITE),
    (C_BLUE, C_WHITE),
    (C_BLACK, C_GOLD),
)

# Messages : (fond, texte)
_STATUS_STYLE = {
    "info": (color565(60, 60, 60), C_WHITE),
    "spin": (C_BLUE, C_WHITE),
    "win": (color565(0, 170, 60), C_WHITE),
    "lose": (C_RED, C_WHITE),
    "warn": (C_ORANGE, C_BLACK),
    "error": (color565(150, 0, 0), C_WHITE),
}

# ----- positions -----
GRID_Y = 86
CELL = 22
ZERO_X = 15
ZERO_W = 24
NUM_X0 = 41                          # 15 + 24 + 2
Y_POINTS, Y_CHIPS, Y_BET, Y_BOTTOM, Y_STATUS = 20, 40, 63, 158, 216


class Backlight:
    """Retro-eclairage de l'ecran commande en PWM (sortie ANALOGIQUE/graduelle)."""

    def __init__(self, gpio):
        self.pwm = None
        if gpio is not None:
            self.pwm = PWM(Pin(gpio), freq=5000, duty_u16=65535)

    def set_percent(self, pct):
        if self.pwm is not None:
            pct = max(0, min(100, pct))
            self.pwm.duty_u16(int(pct * 65535 / 100))


class Screen:
    def __init__(self, tft):
        self.tft = tft
        self.sel = set()       # cases surlignees en jaune (la mise)
        self.ball = None       # case surlignee en blanc (la bille)

    # ---------- ecrans complets ----------
    def draw_splash(self):
        t = self.tft
        t.fill_screen(C_FELT)
        t.fill_rect(0, 90, 320, 60, C_PANEL)
        t.text("ESP32 ROULETTE", 48, 98, C_GOLD, C_PANEL, 2)
        t.text("POINTS GAME", 80, 122, C_WHITE, C_PANEL, 2)
        t.text("STARTING...", 120, 190, C_GREY, C_FELT, 1)

    def draw_sleep(self):
        t = self.tft
        t.fill_screen(C_BLACK)
        t.text("ESP32 ROULETTE", 48, 90, C_GOLD, C_BLACK, 2)
        t.text("SLEEPING...", 80, 125, C_GREY, C_BLACK, 2)
        t.text("MOVE OR PRESS A BUTTON", 68, 165, C_GREY, C_BLACK, 1)

    def draw_all(self, game, active_row, light_pct, pir_text, warning):
        """Redessine tout l'ecran de jeu."""
        t = self.tft
        t.fill_screen(C_FELT)
        self.draw_header(warning)
        self.draw_points(game.balance)
        self.draw_env(light_pct, pir_text)
        self.draw_chips(game.chip_index, active_row == "chip")
        self.draw_bet(game, active_row == "bet")
        self.sel = set()
        self.ball = None
        for n in range(37):
            self.draw_cell(n)
        self.set_selection(game.bet_cells())
        self.draw_last_result(game.history[0] if game.history else None)
        self.draw_history(game.history)

    # ---------- bandeau ----------
    def draw_header(self, warning=""):
        t = self.tft
        t.fill_rect(0, 0, 320, 16, C_HEADER)
        t.text("ESP32 ROULETTE - POINTS GAME", 4, 4, C_BLACK, C_HEADER, 1)
        self.draw_warning(warning)

    def draw_warning(self, text):
        t = self.tft
        if text:
            t.fill_rect(230, 0, 90, 16, C_RED)
            t.text(text, 232, 4, C_WHITE, C_RED, 1)
        else:
            t.fill_rect(230, 0, 90, 16, C_HEADER)

    # ---------- informations ----------
    def draw_points(self, balance):
        t = self.tft
        t.text("POINTS", 6, 24, C_WHITE, C_FELT, 1)
        t.text("%-6d" % balance, 60, 20, C_GOLD, C_FELT, 2)

    def draw_env(self, light_pct, pir_text):
        t = self.tft
        lum = "--" if light_pct is None else "%d" % light_pct
        t.text("LUM %3s%%" % lum, 236, 20, C_GREY, C_FELT, 1)
        t.text("PIR %-4s" % pir_text, 236, 29, C_GREY, C_FELT, 1)

    # ---------- jetons et mise ----------
    def draw_chips(self, chip_index, active):
        t = self.tft
        label_color = C_GOLD if active else C_GREY
        t.text(">CHIP" if active else " CHIP", 2, 46, label_color, C_FELT, 1)
        for i, value in enumerate(config.CHIPS):
            x = 66 + i * 62
            bg, fg = _CHIP_STYLE[i]
            t.fill_rect(x - 2, Y_CHIPS - 1, 60, 22, C_FELT)     # efface l'ancien cadre
            t.fill_rect(x, Y_CHIPS, 56, 20, bg)
            txt = str(value)
            t.text(txt, x + (56 - len(txt) * 16) // 2, Y_CHIPS + 2, fg, bg, 2)
            if i == chip_index:
                t.rect(x - 2, Y_CHIPS - 1, 60, 22, C_GOLD if active else C_WHITE, 2)

    def draw_bet(self, game, active):
        t = self.tft
        t.fill_rect(0, Y_BET, 320, 20, C_FELT)
        t.text(">BET" if active else " BET", 2, Y_BET + 6, C_GOLD if active else C_GREY, C_FELT, 1)
        swatch = _CELL_COLORS[game.bet_color()]
        t.fill_rect(66, Y_BET + 1, 22, 16, swatch)
        t.rect(66, Y_BET + 1, 22, 16, C_WHITE, 1)
        t.text(game.bet_name(), 94, Y_BET + 1, C_WHITE, C_FELT, 2)
        t.text("PAYS X%d" % game.multiplier(), 252, Y_BET + 6, C_GREY, C_FELT, 1)

    # ---------- grille ----------
    def _geometry(self, n):
        if n == 0:
            return ZERO_X, GRID_Y, ZERO_W, 3 * CELL
        col = (n - 1) // 3
        row = 2 - ((n - 1) % 3)        # la rangee du haut contient 3, 6, 9 ...
        return NUM_X0 + col * CELL, GRID_Y + row * CELL, CELL, CELL

    def draw_cell(self, n):
        t = self.tft
        x, y, w, h = self._geometry(n)
        color = _CELL_COLORS[color_of(n)]
        t.fill_rect(x, y, w, h, C_FELT)
        t.fill_rect(x + 1, y + 1, w - 2, h - 2, color)
        label = str(n)
        scale = 2 if n == 0 else 1
        tw, th = len(label) * 8 * scale, 8 * scale
        t.text(label, x + (w - tw) // 2, y + (h - th) // 2, C_WHITE, color, scale)
        if n == self.ball:
            t.rect(x, y, w, h, C_WHITE, 2)
        elif n in self.sel:
            t.rect(x, y, w, h, C_GOLD, 2)

    def set_selection(self, cells):
        """Surligne en jaune les cases de la mise."""
        new = set(cells)
        changed = self.sel ^ new
        self.sel = new
        for n in changed:
            self.draw_cell(n)

    def set_ball(self, n):
        """Surligne en blanc la case de la 'bille' (None pour l'enlever)."""
        old = self.ball
        self.ball = n
        if old is not None and old != n:
            self.draw_cell(old)
        if n is not None:
            self.draw_cell(n)

    # ---------- resultat et historique ----------
    def draw_last_result(self, number):
        t = self.tft
        t.text("LAST", 6, Y_BOTTOM, C_WHITE, C_FELT, 1)
        if number is None:
            t.fill_rect(6, 168, 72, 44, C_PANEL)
            t.text("--", 6 + 12, 168 + 10, C_GREY, C_PANEL, 3)
            return
        color = _CELL_COLORS[color_of(number)]
        t.fill_rect(6, 168, 72, 44, color)
        txt = str(number)
        t.text(txt, 6 + (72 - len(txt) * 24) // 2, 168 + 10, C_WHITE, color, 3)

    def draw_history(self, history):
        t = self.tft
        t.text("HISTORY", 90, Y_BOTTOM, C_WHITE, C_FELT, 1)
        for i in range(config.HISTORY_SIZE):
            x = 90 + (i % 8) * 28
            y = 170 + (i // 8) * 22
            if i < len(history):
                n = history[i]
                color = _CELL_COLORS[color_of(n)]
                t.fill_rect(x, y, 26, 20, color)
                txt = str(n)
                t.text(txt, x + (26 - len(txt) * 8) // 2, y + 6, C_WHITE, color, 1)
            else:
                t.fill_rect(x, y, 26, 20, C_PANEL)

    # ---------- message ----------
    def draw_status(self, text, kind="info"):
        t = self.tft
        bg, fg = _STATUS_STYLE[kind]
        t.fill_rect(0, Y_STATUS, 320, 24, bg)
        text = text[:20]
        t.text(text, (320 - len(text) * 16) // 2, Y_STATUS + 4, fg, bg, 2)


def create_screen():
    """Construit le SPI, le pilote et l'interface. Leve OSError si l'ecran est absent."""
    spi = None
    for bus_id in (1, 2):
        try:
            spi = SPI(bus_id, baudrate=config.TFT_BAUDRATE, polarity=0, phase=0,
                      sck=Pin(config.PIN_TFT_SCK), mosi=Pin(config.PIN_TFT_MOSI),
                      miso=Pin(config.PIN_TFT_MISO))
            break
        except (ValueError, OSError):
            spi = None
    if spi is None:
        raise OSError("SPI indisponible")
    try:
        tft = ILI9341(spi, Pin(config.PIN_TFT_CS, Pin.OUT), Pin(config.PIN_TFT_DC, Pin.OUT),
                      Pin(config.PIN_TFT_RST, Pin.OUT), madctl=config.TFT_MADCTL,
                      check_id=config.TFT_CHECK_ID)
    except Exception:
        spi.deinit()                      # on libere le bus avant la prochaine tentative
        raise
    return Screen(tft)
