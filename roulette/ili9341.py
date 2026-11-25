"""
ili9341.py - Pilote minimal pour l'ecran TFT ILI9341 (320 x 240) en SPI.

Ce pilote sait seulement :
  - initialiser l'ecran (sequence classique du fabricant)
  - tester si l'ecran repond (lecture de son identifiant)
  - dessiner des rectangles pleins ou vides
  - ecrire du texte (police 8x8 integree a MicroPython, agrandissable)
Les couleurs sont en RGB565 (16 bits) : utiliser color565(r, g, b).
"""
import time
import framebuf


def color565(r, g, b):
    """Convertit un RGB 8 bits en un entier RGB565."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class ILI9341:
    def __init__(self, spi, cs, dc, rst=None, madctl=0x28, check_id=True):
        # spi, cs, dc, rst : objets machine.SPI / machine.Pin deja crees
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.width = 320
        self.height = 240
        self.madctl = madctl
        self.check_id = check_id
        self.id = b""
        self._glyphs = {}   # cache : une rangee de pixels d'une lettre
        self.cs.value(1)
        self._reset()
        self._check_present()
        self._init_display()

    # ---------- communication bas niveau ----------
    def _cmd(self, cmd, data=None):
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytes((cmd,)))
        if data:
            self.dc.value(1)
            self.spi.write(data)
        self.cs.value(1)

    def _reset(self):
        if self.rst is not None:
            self.rst.value(1)
            time.sleep_ms(10)
            self.rst.value(0)
            time.sleep_ms(20)
            self.rst.value(1)
        else:
            self._cmd(0x01)  # reset logiciel
        time.sleep_ms(150)

    def read_id(self):
        """Lit l'identifiant ILI9341 (commande 0xD3). Un vrai ILI9341 repond 00 93 41."""
        buf = bytearray(4)
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(b"\xD3")
        self.dc.value(1)
        self.spi.readinto(buf)
        self.cs.value(1)
        return bytes(buf)

    def _check_present(self):
        """Leve OSError si l'ecran ne repond pas (debranche, mauvais fil...)."""
        if not self.check_id:
            return
        self.id = self.read_id()
        print("TFT id:", self.id)
        if self.id == b"\xff\xff\xff\xff":
            # Ligne MISO jamais tiree a 0 : fil SDO absent/mal branche, ou ecran debranche
            raise OSError("Aucune reponse sur MISO (fil SDO -> D12 ?) - lancer tft_diag.py")
        if self.id == b"\x00\x00\x00\x00":
            raise OSError("Ecran ILI9341 absent (aucune reponse)")

    def _init_display(self):
        init = (
            (0xCF, b"\x00\xC1\x30"),
            (0xED, b"\x64\x03\x12\x81"),
            (0xE8, b"\x85\x00\x78"),
            (0xCB, b"\x39\x2C\x00\x34\x02"),
            (0xF7, b"\x20"),
            (0xEA, b"\x00\x00"),
            (0xC0, b"\x23"),
            (0xC1, b"\x10"),
            (0xC5, b"\x3E\x28"),
            (0xC7, b"\x86"),
            (0x36, bytes((self.madctl,))),   # orientation / ordre des couleurs
            (0x3A, b"\x55"),                 # 16 bits par pixel
            (0xB1, b"\x00\x18"),
            (0xB6, b"\x08\x82\x27"),
            (0xF2, b"\x00"),
            (0x26, b"\x01"),
            (0xE0, b"\x0F\x31\x2B\x0C\x0E\x08\x4E\xF1\x37\x07\x10\x03\x0E\x09\x00"),
            (0xE1, b"\x00\x0E\x14\x03\x11\x07\x31\xC1\x48\x08\x0F\x0C\x31\x36\x0F"),
        )
        for cmd, data in init:
            self._cmd(cmd, data)
        self._cmd(0x11)          # sortie de veille
        time.sleep_ms(120)
        self._cmd(0x29)          # affichage ON
        time.sleep_ms(20)

    # ---------- dessin ----------
    def _window(self, x0, y0, x1, y1):
        self._cmd(0x2A, bytes((x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF)))
        self._cmd(0x2B, bytes((y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF)))
        self._cmd(0x2C)

    def fill_rect(self, x, y, w, h, color):
        # on coupe ce qui depasse de l'ecran
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0
        if x + w > self.width:
            w = self.width - x
        if y + h > self.height:
            h = self.height - y
        if w <= 0 or h <= 0:
            return
        self._window(x, y, x + w - 1, y + h - 1)
        px = bytes((color >> 8, color & 0xFF))
        total = w * h
        chunk = min(total, 512)
        block = px * chunk
        self.cs.value(0)
        self.dc.value(1)
        while total > 0:
            if total >= chunk:
                self.spi.write(block)
                total -= chunk
            else:
                self.spi.write(px * total)
                total = 0
        self.cs.value(1)

    def fill_screen(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def rect(self, x, y, w, h, color, thick=1):
        """Contour de rectangle (epaisseur en pixels, vers l'interieur)."""
        self.fill_rect(x, y, w, thick, color)
        self.fill_rect(x, y + h - thick, w, thick, color)
        self.fill_rect(x, y, thick, h, color)
        self.fill_rect(x + w - thick, y, thick, h, color)

    def _glyph_row(self, byte, fg, bg, scale):
        """Pixels (RGB565) d'une rangee de 8 points d'une lettre, agrandie 'scale' fois."""
        key = (byte, fg, bg, scale)
        row = self._glyphs.get(key)
        if row is None:
            if len(self._glyphs) > 400:
                self._glyphs.clear()
            fgb = bytes((fg >> 8, fg & 0xFF))
            bgb = bytes((bg >> 8, bg & 0xFF))
            out = bytearray()
            for bit in range(7, -1, -1):
                out += (fgb if (byte >> bit) & 1 else bgb) * scale
            row = bytes(out)
            self._glyphs[key] = row
        return row

    def text(self, s, x, y, fg, bg, scale=1):
        """Ecrit du texte ASCII (fond 'bg' obligatoire). Largeur d'une lettre = 8*scale px."""
        n = len(s)
        maxn = (self.width - x) // (8 * scale)
        if n > maxn:
            s = s[:maxn]
            n = maxn
        if n <= 0 or y + 8 * scale > self.height:
            return
        # La police 8x8 de MicroPython sert a dessiner le texte dans un petit tampon 1 bit
        mono = bytearray(n * 8)
        fb = framebuf.FrameBuffer(mono, n * 8, 8, framebuf.MONO_HLSB)
        fb.text(s, 0, 0, 1)
        self._window(x, y, x + n * 8 * scale - 1, y + 8 * scale - 1)
        self.cs.value(0)
        self.dc.value(1)
        for row in range(8):
            line = bytearray()
            for i in range(n):
                line += self._glyph_row(mono[row * n + i], fg, bg, scale)
            for _ in range(scale):
                self.spi.write(line)
        self.cs.value(1)
