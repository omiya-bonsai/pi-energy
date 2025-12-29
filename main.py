from machine import Pin, SPI
import framebuf
import time
import math

# ========= display =========
ROTATE_CW = True

# ========= timing =========
TARGET_FPS = 10
FRAME_MS = int(1000 / TARGET_FPS)
TERMS_PER_FRAME = 7000

# ========= digits/min window =========
RATE_WINDOW_MS = 60_000
RATE_MIN_VALID_MS = 10_000


def clamp01(x):
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def bar(fb, x, y, w, h, ratio):
    fb.rect(x, y, w, h, 1)
    fill = int((w - 2) * clamp01(ratio))
    if fill > 0:
        fb.fill_rect(x + 1, y + 1, fill, h - 2, 1)


def spinner_char(t):
    return "|/-\\"[t & 3]


def fmt_time(secs):
    s = int(secs)
    m = s // 60
    s = s % 60
    return "{:02d}:{:02d}".format(m, s)


def stable_digits(err):
    if err <= 0:
        return 15
    d = int(-math.log10(err))
    if d < 0:
        d = 0
    if d > 15:
        d = 15
    return d


# ---------- SH1107 SPI (rotated) ----------
class SH1107_SPI_Rot90:
    def __init__(self, spi, cs, dc, rst=None):
        self.dev_w = 64
        self.dev_h = 128
        self.dev_pages = self.dev_h // 8
        self.dev_buf = bytearray(self.dev_w * self.dev_pages)

        self.w = 128
        self.h = 64
        self.draw_buf = bytearray(self.w * (self.h // 8))
        self.fb = framebuf.FrameBuffer(self.draw_buf, self.w, self.h, framebuf.MONO_VLSB)

        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst

        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        if rst:
            rst.init(Pin.OUT, value=1)
            self.reset()

        self.init_display()
        self.clear()
        self.show()

    def reset(self):
        self.rst.value(1); time.sleep_ms(10)
        self.rst.value(0); time.sleep_ms(20)
        self.rst.value(1); time.sleep_ms(20)

    def write_cmd(self, c):
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytes([c]))
        self.cs.value(1)

    def write_data(self, d):
        self.cs.value(0)
        self.dc.value(1)
        self.spi.write(d)
        self.cs.value(1)

    def init_display(self):
        for c in [
            0xAE, 0xDC, 0x00, 0x81, 0x7F, 0xA0, 0xC0,
            0xA8, 0x7F, 0xD3, 0x60, 0xD5, 0x51,
            0xD9, 0x22, 0xDB, 0x35, 0xAD, 0x8A,
            0xA4, 0xA6, 0xAF
        ]:
            self.write_cmd(c)

    def clear(self):
        self.fb.fill(0)

    def _set_pixel(self, x, y):
        idx = x + (y >> 3) * self.dev_w
        self.dev_buf[idx] |= (1 << (y & 7))

    def _rotate(self):
        for i in range(len(self.dev_buf)):
            self.dev_buf[i] = 0
        for y in range(self.h):
            for x in range(self.w):
                if self.fb.pixel(x, y):
                    dx = y
                    dy = 127 - x if ROTATE_CW else x
                    self._set_pixel(dx, dy)

    def show(self):
        self._rotate()
        for p in range(self.dev_pages):
            self.write_cmd(0xB0 | p)
            self.write_cmd(0x00)
            self.write_cmd(0x10)
            s = p * self.dev_w
            self.write_data(self.dev_buf[s:s + self.dev_w])


# ---------- hardware ----------
spi = SPI(
    1, baudrate=20_000_000, polarity=1, phase=1,
    sck=Pin(10), mosi=Pin(11)
)

oled = SH1107_SPI_Rot90(
    spi, cs=Pin(9), dc=Pin(8), rst=Pin(12)
)

# ---------- pi calculation ----------
pi_est = 3.0
n = 2
sign = 1.0

t0 = time.ticks_ms()
t_last = t0

ema_ips = 0.0
hist_max = 1.0

hist_t = []
hist_d = []

spin = 0

while True:
    frame_start = time.ticks_ms()

    # compute
    for _ in range(TERMS_PER_FRAME):
        pi_est += sign * (4.0 / (n * (n + 1) * (n + 2)))
        sign = -sign
        n += 2

    now = time.ticks_ms()
    elapsed_s = time.ticks_diff(now, t0) / 1000.0

    # energy
    dt = max(1e-6, time.ticks_diff(now, t_last) / 1000.0)
    ips = TERMS_PER_FRAME / dt
    ema_ips = ips if ema_ips == 0 else 0.8 * ema_ips + 0.2 * ips
    t_last = now

    if ema_ips > hist_max:
        hist_max = ema_ips
    hist_max *= 0.995
    energy = ema_ips / max(hist_max, 1.0)

    # digits
    err = abs(pi_est - math.pi)
    digits = stable_digits(err)

    # digits/min
    hist_t.append(now)
    hist_d.append(digits)
    cutoff = now - RATE_WINDOW_MS
    while hist_t and hist_t[0] < cutoff:
        hist_t.pop(0)
        hist_d.pop(0)

    dpm = 0.0
    if elapsed_s * 1000 > RATE_MIN_VALID_MS and len(hist_t) > 1:
        dtm = time.ticks_diff(now, hist_t[0])
        if dtm > 0:
            dpm = (digits - hist_d[0]) * 60000 / dtm

    # draw
    fb = oled.fb
    oled.clear()

    fb.text("Pi ENERGY", 0, 0, 1)
    fb.text(spinner_char(spin), 120, 0, 1)
    spin += 1

    fb.text("digits : {}".format(digits), 0, 12, 1)
    fb.text("time   : {}".format(fmt_time(elapsed_s)), 0, 24, 1)
    fb.text("digits/min : {:.1f}".format(max(0.0, dpm)), 0, 36, 1)
    fb.text("energy", 0, 48, 1)

    bar(fb, 0, 58, 128, 6, energy)

    oled.show()

    used = time.ticks_diff(time.ticks_ms(), frame_start)
    if used < FRAME_MS:
        time.sleep_ms(FRAME_MS - used)

