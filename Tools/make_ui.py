import math
import os

from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Assets", "Art", "UI")
SS = 4


def canvas(size):
    return Image.new("RGBA", (size * SS, size * SS), (255, 255, 255, 0))


def save(img, name, size):
    img.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name))


def rounded(size=128, radius=48):
    img = canvas(size)
    ImageDraw.Draw(img).rounded_rectangle([0, 0, size * SS - 1, size * SS - 1], radius * SS, fill="white")
    save(img, "Rounded.png", size)


def shadow(size=128, radius=40, blur=14):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    m = blur + 4
    ImageDraw.Draw(img).rounded_rectangle([m, m, size - m, size - m], radius - m // 2, fill=(255, 255, 255, 255))
    img.filter(ImageFilter.GaussianBlur(blur)).save(os.path.join(OUT, "Shadow.png"))


def circle(size=64):
    img = canvas(size)
    ImageDraw.Draw(img).ellipse([0, 0, size * SS - 1, size * SS - 1], fill="white")
    save(img, "Circle.png", size)


def glow(size=128):
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    px = img.load()
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / c
            px[x, y] = (255, 255, 255, int(255 * max(0.0, 1 - d) ** 2.2))
    img.save(os.path.join(OUT, "Glow.png"))


def star_points(cx, cy, r_out, r_in, n=5):
    return [(cx + (r_out if i % 2 == 0 else r_in) * math.cos(math.radians(-90 + 180 * i / n)),
             cy + (r_out if i % 2 == 0 else r_in) * math.sin(math.radians(-90 + 180 * i / n))) for i in range(2 * n)]


def star(size=128):
    img = canvas(size)
    s = size * SS
    ImageDraw.Draw(img).polygon(star_points(s / 2, s * 0.53, s * 0.47, s * 0.2), fill="white")
    save(img, "Star.png", size)


def check(size=128):
    img = canvas(size)
    d = ImageDraw.Draw(img)
    s = size * SS
    pts = [(0.16 * s, 0.55 * s), (0.4 * s, 0.8 * s), (0.86 * s, 0.2 * s)]
    d.line(pts, fill="white", width=int(0.12 * s), joint="curve")
    for p in (pts[0], pts[-1]):
        r = 0.06 * s
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill="white")
    import random
    random.seed(7)
    for _ in range(260):
        x, y, r = random.uniform(0, s), random.uniform(0, s), random.uniform(0.004, 0.012) * s
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 0))
    save(img, "Check.png", size)


def icon(name, draw, size=128):
    img = canvas(size)
    draw(ImageDraw.Draw(img), size * SS)
    save(img, f"Icon_{name}.png", size)


def icons():
    w = lambda s: int(0.1 * s)

    icon("Play", lambda d, s: d.polygon([(0.3 * s, 0.18 * s), (0.82 * s, 0.5 * s), (0.3 * s, 0.82 * s)], fill="white"))
    icon("Pause", lambda d, s: [d.rounded_rectangle([x * s, 0.2 * s, (x + 0.16) * s, 0.8 * s], 0.04 * s, fill="white")
                                for x in (0.27, 0.57)])

    def restart(d, s):
        d.arc([0.2 * s, 0.2 * s, 0.8 * s, 0.8 * s], 40, 320, fill="white", width=w(s))
        a = math.radians(40)
        tip = (0.5 * s + 0.3 * s * math.cos(a), 0.5 * s + 0.3 * s * math.sin(a))
        d.polygon([(tip[0] + 0.13 * s, tip[1] - 0.02 * s), (tip[0] - 0.1 * s, tip[1] - 0.1 * s),
                   (tip[0] - 0.02 * s, tip[1] + 0.14 * s)], fill="white")
    icon("Restart", restart)

    def home(d, s):
        d.polygon([(0.5 * s, 0.16 * s), (0.86 * s, 0.48 * s), (0.14 * s, 0.48 * s)], fill="white")
        d.rectangle([0.24 * s, 0.46 * s, 0.76 * s, 0.84 * s], fill="white")
        d.rectangle([0.43 * s, 0.6 * s, 0.57 * s, 0.84 * s], fill=(255, 255, 255, 0))
    icon("Home", home)

    def quit_icon(d, s):
        d.line([(0.25 * s, 0.25 * s), (0.75 * s, 0.75 * s)], fill="white", width=w(s))
        d.line([(0.75 * s, 0.25 * s), (0.25 * s, 0.75 * s)], fill="white", width=w(s))
    icon("Quit", quit_icon)

    def controls(d, s):
        d.rounded_rectangle([0.1 * s, 0.3 * s, 0.9 * s, 0.72 * s], 0.2 * s, fill="white")
        clear = (255, 255, 255, 0)
        d.rectangle([0.22 * s, 0.47 * s, 0.38 * s, 0.53 * s], fill=clear)
        d.rectangle([0.27 * s, 0.42 * s, 0.33 * s, 0.58 * s], fill=clear)
        for cx, cy in ((0.66, 0.44), (0.74, 0.56)):
            r = 0.05 * s
            d.ellipse([cx * s - r, cy * s - r, cx * s + r, cy * s + r], fill=clear)
    icon("Controls", controls)

    icon("Back", lambda d, s: d.line([(0.62 * s, 0.2 * s), (0.32 * s, 0.5 * s), (0.62 * s, 0.8 * s)], fill="white",
                                     width=w(s), joint="curve"))

    def hint(d, s):
        d.ellipse([0.1 * s, 0.12 * s, 0.9 * s, 0.76 * s], fill="white")
        d.polygon([(0.3 * s, 0.68 * s), (0.22 * s, 0.9 * s), (0.48 * s, 0.73 * s)], fill="white")
        clear = (255, 255, 255, 0)
        for cx in (0.32, 0.5, 0.68):
            r = 0.055 * s
            d.ellipse([cx * s - r, 0.44 * s - r, cx * s + r, 0.44 * s + r], fill=clear)
    icon("Hint", hint)


def main():
    os.makedirs(OUT, exist_ok=True)
    rounded()
    shadow()
    circle()
    glow()
    star()
    check()
    icons()
    print("UI sprites written to", OUT)


if __name__ == "__main__":
    main()
