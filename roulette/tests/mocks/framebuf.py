MONO_HLSB = 3


class FrameBuffer:
    def __init__(self, buf, w, h, fmt):
        self.buf = buf

    def text(self, s, x, y, c=1):
        for i in range(len(self.buf)):
            self.buf[i] = 0xAA
