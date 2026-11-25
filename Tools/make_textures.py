import os

import numpy as np
from PIL import Image

N = 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Assets", "Art", "Textures")
rng = np.random.default_rng(7)

ky, kx = np.meshgrid(np.fft.fftfreq(N) * N, np.fft.fftfreq(N) * N, indexing="ij")
ys, xs = np.mgrid[0:N, 0:N].astype(np.float32)


def noise(sigma_x, sigma_y=None, seed=None):
    sigma_y = sigma_x if sigma_y is None else sigma_y
    r = np.random.default_rng(seed) if seed is not None else rng
    white = r.standard_normal((N, N))
    filt = np.exp(-2 * np.pi ** 2 * ((kx * sigma_x / N) ** 2 + (ky * sigma_y / N) ** 2))
    field = np.real(np.fft.ifft2(np.fft.fft2(white) * filt))
    field -= field.min()
    return field / field.max()


def fbm(base_sigma, octaves=4, aniso=1.0, seed=None):
    total, amp, weight = np.zeros((N, N)), 1.0, 0.0
    for i in range(octaves):
        s = base_sigma / (2 ** i)
        total += amp * noise(s, s * aniso, None if seed is None else seed + i)
        weight += amp
        amp *= 0.5
    return total / weight


def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def normal_from_height(height, strength):
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * strength
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * strength
    n = np.stack([-dx, dy, np.ones_like(height)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return (n + 1) * 0.5


def save(name, albedo, height=None, strength=4.0):
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray((np.clip(albedo, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, f"{name}_albedo.png"))
    if height is not None:
        Image.fromarray((normal_from_height(height, strength) * 255).astype(np.uint8)).save(
            os.path.join(OUT, f"{name}_normal.png"))
    print("saved", name)


def wood(light, dark, lines=26, seed=1):
    warp = fbm(220, 3, aniso=6, seed=seed)
    rings = 0.5 + 0.5 * np.sin(2 * np.pi * (lines * xs / N + 5.0 * warp + 0.6 * fbm(60, 2, aniso=4, seed=seed + 3)))
    grain = rings ** 2.5
    fine = noise(1.5, 30, seed=seed + 10)
    t = 0.75 * grain + 0.25 * fine
    albedo = mix(light, dark, t) * (0.92 + 0.08 * fbm(300, 2, seed=seed + 20))[..., None]
    return albedo, 0.6 * (1 - grain) + 0.4 * fine


oak_albedo, oak_height = wood((0.80, 0.62, 0.42), (0.56, 0.38, 0.22), seed=1)
save("wood_oak", oak_albedo, oak_height, 2.5)
walnut_albedo, walnut_height = wood((0.42, 0.27, 0.16), (0.22, 0.13, 0.08), seed=5)
save("wood_walnut", walnut_albedo, walnut_height, 2.5)

plank_w = N // 8
floor_albedo = np.zeros((N, N, 3))
floor_height = np.zeros((N, N))
for p in range(8):
    a, h = wood((0.58, 0.42, 0.28), (0.36, 0.24, 0.15), lines=26, seed=30 + p)
    cols = slice(p * plank_w, (p + 1) * plank_w)
    tone = rng.uniform(0.85, 1.1)
    floor_albedo[:, cols] = a[:, cols] * tone
    floor_height[:, cols] = h[:, cols]
    joint = int(rng.uniform(0, N))
    for y in range(joint - 2, joint + 2):
        floor_albedo[y % N, cols] *= 0.45
        floor_height[y % N, cols] = 0
seam = (xs % plank_w < 3)
floor_albedo[seam] *= 0.4
floor_height[seam] = 0
save("wood_floor", floor_albedo, floor_height, 3.0)

rows, per_row = 14, 4
row_h, brick_w = N / rows, N / per_row
row = (ys // row_h).astype(int)
offset = np.where(row % 2 == 1, brick_w / 2, 0)
col = (((xs + offset) % N) // brick_w).astype(int)
brick_id = row * per_row + col
tones = rng.uniform(0.75, 1.15, rows * per_row)
hues = rng.uniform(-0.04, 0.04, rows * per_row)
mortar = ((ys % row_h) < 5) | (((xs + offset) % brick_w) < 5)
base = np.stack([0.58 + hues[brick_id], 0.27 + hues[brick_id] * 0.5, 0.19 * np.ones((N, N))], -1) * tones[brick_id][..., None]
grit = fbm(8, 3, seed=50)
brick_albedo = base * (0.85 + 0.25 * grit)[..., None]
brick_albedo[mortar] = (np.array([0.66, 0.63, 0.58]) * (0.9 + 0.1 * grit[mortar])[..., None])
brick_height = np.where(mortar, 0.0, 0.8 + 0.2 * grit)
save("brick", brick_albedo, brick_height, 6.0)

blotch = fbm(260, 4, seed=60)
speck = noise(1.2, seed=61)
plaster_albedo = np.array([0.88, 0.83, 0.74]) * (0.86 + 0.12 * blotch + 0.04 * speck)[..., None]
save("plaster", plaster_albedo, 0.7 * fbm(30, 3, seed=62) + 0.3 * speck, 1.5)

streaks = noise(1.2, 60, seed=70)
metal_albedo = np.repeat((0.75 + 0.2 * streaks + 0.05 * fbm(200, 2, seed=71))[..., None], 3, -1)
save("metal", metal_albedo, streaks, 1.0)

weave = 0.5 + 0.25 * (np.sin(2 * np.pi * 96 * xs / N) + np.sin(2 * np.pi * 96 * ys / N))
fuzz = noise(2, seed=80)
fabric_albedo = np.repeat((0.78 + 0.14 * weave + 0.08 * fuzz)[..., None], 3, -1)
save("fabric", fabric_albedo, 0.7 * weave + 0.3 * fuzz, 3.0)

cells = fbm(6, 3, seed=90)
leather_albedo = np.repeat((0.75 + 0.2 * cells + 0.05 * fbm(250, 2, seed=91))[..., None], 3, -1)
save("leather", leather_albedo, cells, 2.5)

enamel_albedo = np.repeat((0.94 + 0.05 * fbm(120, 3, seed=100))[..., None], 3, -1)
save("enamel", enamel_albedo, fbm(40, 2, seed=101), 0.6)

pitch = N / 16
hx, hy = (xs % pitch) - pitch / 2, (ys % pitch) - pitch / 2
hole = (hx ** 2 + hy ** 2) < (pitch * 0.14) ** 2
peg_albedo = np.array([0.72, 0.56, 0.38]) * (0.9 + 0.1 * fbm(60, 3, seed=110))[..., None]
peg_albedo[hole] = (0.08, 0.06, 0.05)
save("pegboard", peg_albedo, np.where(hole, 0.0, 1.0), 4.0)

glow = fbm(25, 4, seed=120)
embers_albedo = mix((0.15, 0.03, 0.01), (1.0, 0.45, 0.08), glow ** 1.5)
save("embers", embers_albedo)

W, H = 1024, 1024
v = np.linspace(1, 0, H)[:, None] * np.ones((1, W))
sky = mix((0.02, 0.03, 0.08), (0.07, 0.10, 0.22), v)
star_mask = rng.random((H, W)) > 0.9985
sky[star_mask & (v > 0.35)] = (0.9, 0.92, 1.0)
yy, xx = np.mgrid[0:H, 0:W]
moon_d = np.sqrt((xx - 700) ** 2 + (yy - 260) ** 2)
sky = mix(sky, (0.95, 0.93, 0.85), np.clip((70 - moon_d) / 3, 0, 1))
sky += (np.exp(-(moon_d / 180) ** 2) * 0.12)[..., None] * np.array([0.6, 0.65, 0.8])
hills = 0.22 + 0.05 * np.sin(xx / 140.0) + 0.03 * np.sin(xx / 47.0 + 1.3)
sky[(yy / H) > (1 - hills)] = (0.75, 0.80, 0.90)
roofs = np.zeros(W)
for start in range(0, W, 90):
    width, height = int(rng.uniform(50, 80)), rng.uniform(0.10, 0.17)
    xs_house = np.arange(start, min(W, start + width))
    peak = width * 0.45
    roof_shape = height + 0.07 * (1 - np.abs(xs_house - start - width / 2) / (width / 2))
    roofs[xs_house] = np.maximum(roofs[xs_house], roof_shape)
house = (yy / H) > (1 - roofs[None, :]) - 0.0
sky[house] = (0.05, 0.05, 0.09)
window_lights = house & (rng.random((H, W)) > 0.9993)
for y, x in zip(*np.nonzero(window_lights)):
    sky[max(0, y - 4):y + 4, max(0, x - 3):x + 3] = (1.0, 0.8, 0.4)
save("night_sky", sky)
