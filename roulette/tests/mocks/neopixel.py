class NeoPixel:
    def __init__(self, pin, n):
        self.n = n
        self.px = [(0, 0, 0)] * n

    def __setitem__(self, i, v):
        self.px[i] = v

    def __getitem__(self, i):
        return self.px[i]

    def write(self):
        pass
