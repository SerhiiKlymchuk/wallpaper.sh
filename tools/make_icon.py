"""32x32 pixel-art app icon: a painter at work on a happy little landscape."""
import sys
from pathlib import Path
from PIL import Image

N = 32
PAL = {
    "K": "#1b1323",  # outline
    "A": "#5b3421", "a": "#80502f",                 # afro + highlight
    "S": "#f2b48c", "s": "#cf8763",                 # skin + shade
    "B": "#4a2a1a", "r": "#b5544c",                 # beard, mouth
    "D": "#8fb6e3", "d": "#5f88c2",                 # denim shirt + shade
    "E": "#9a6332", "e": "#62391a",                 # easel wood
    "C": "#f6efe2",                                 # canvas frame
    "L": "#79c9ff", "l": "#b7e6ff", "w": "#ffffff", # sky, light sky, cloud/snow
    "M": "#6a6f9a", "m": "#4b5079",                 # mountains
    "G": "#2f9a4c", "g": "#1e6a35", "H": "#63c14d", # tree, grass
    "P": "#d9a066", "R": "#e8402e", "Y": "#ffd23f", "U": "#3f6fe8",
}
BG = ["#2a1b45", "#3d2156", "#5a275f", "#7e2e5e", "#a83a55", "#d24a43", "#f0612f", "#ff8a3d"]

grid = [[None] * N for _ in range(N)]
sprite = [[False] * N for _ in range(N)]

def put(x, y, c, spr=True):
    if 0 <= x < N and 0 <= y < N:
        grid[y][x] = c
        sprite[y][x] = sprite[y][x] or spr

def rect(x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(x, y, c)

def disc(cx, cy, rx, ry, c):
    for y in range(N):
        for x in range(N):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                put(x, y, c)

# --- easel -----------------------------------------------------------------
for i, y in enumerate(range(20, 30)):
    put(5 - i // 4, y, "E"); put(14 + i // 4, y, "E")
rect(9, 20, 10, 28, "e")
rect(2, 20, 17, 20, "e")
rect(8, 3, 11, 3, "e")

# --- canvas with a happy little landscape ------------------------------------
rect(3, 4, 16, 19, "C")
rect(4, 5, 15, 13, "L")
rect(4, 5, 15, 6, "l")
rect(11, 6, 13, 6, "w"); rect(10, 7, 14, 7, "w")          # cloud
for y in range(8, 16):                                     # big mountain
    h = y - 8
    for x in range(8 - h, 9 + h):
        if 4 <= x <= 15:
            put(x, y, "w" if y <= 9 else ("m" if x > 8 else "M"))
for y in range(10, 16):                                    # small mountain
    h = y - 10
    for x in range(13 - h, 14 + h):
        if 4 <= x <= 15:
            put(x, y, "m" if x > 13 else "M")
rect(4, 14, 15, 18, "H")
rect(4, 17, 15, 18, "g")
for y, half in ((9, 0), (10, 1), (11, 1), (12, 2), (13, 2), (14, 3), (15, 3)):  # happy little tree
    for x in range(6 - half, 7 + half):
        if 4 <= x <= 15:
            put(x, y, "g" if x > 6 else "G")
rect(6, 16, 6, 17, "e")

# --- Bob ---------------------------------------------------------------------
disc(24.8, 9.0, 7.9, 7.6, "A")
for y in range(N):                                        # curly texture
    for x in range(N):
        if grid[y][x] == "A" and (x * 3 + y * 5) % 7 == 0:
            put(x, y, "a")
for x, y in ((20, 3), (21, 2), (22, 2), (19, 4), (18, 6), (18, 7)):
    put(x, y, "a")
rect(21, 7, 28, 15, "S")
for x, y in ((21, 7), (28, 7)):
    put(x, y, "A")
rect(22, 10, 22, 10, "K"); rect(27, 10, 27, 10, "K")      # eyes
rect(24, 11, 25, 12, "s")                                 # nose
rect(21, 12, 21, 15, "B"); rect(28, 12, 28, 15, "B")      # beard sides
rect(23, 13, 26, 13, "B")                                 # mustache
rect(21, 14, 28, 15, "B"); rect(24, 14, 25, 14, "r")      # beard + smile
rect(22, 16, 27, 16, "B")
rect(19, 17, 31, 31, "D")                                 # shirt
rect(29, 18, 31, 31, "d")
rect(23, 17, 26, 17, "S"); rect(24, 18, 25, 18, "S")      # open collar
rect(22, 17, 22, 19, "d"); rect(27, 17, 27, 19, "d")
# painting arm reaching to the canvas
for x, y in ((19, 19), (18, 19), (18, 18), (17, 18), (17, 17)):
    put(x, y, "D")
rect(16, 16, 17, 16, "S")
for x, y in ((15, 15), (14, 14)):
    put(x, y, "e")
put(13, 13, "Y")
# palette in the other hand
disc(27.5, 25.5, 3.6, 2.3, "P")
put(26, 25, "R"); put(28, 24, "Y"); put(29, 26, "U"); put(27, 26, "G")
rect(24, 26, 25, 27, "S")

# --- outline around everything drawn -----------------------------------------
outline = []
for y in range(N):
    for x in range(N):
        if grid[y][x] is None and any(
            0 <= x + dx < N and 0 <= y + dy < N and sprite[y + dy][x + dx]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            outline.append((x, y))
for x, y in outline:
    grid[y][x] = "K"

# --- render ------------------------------------------------------------------
def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)

img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
corner = {(0, 0), (1, 0), (0, 1), (2, 0), (0, 2), (1, 1)}
for y in range(N):
    band = min(len(BG) - 1, y * len(BG) // N)
    nxt = min(len(BG) - 1, band + 1)
    edge = (y + 1) % (N // len(BG)) == 0                 # dither the band edges
    for x in range(N):
        cx, cy = min(x, N - 1 - x), min(y, N - 1 - y)
        if (cx, cy) in corner:
            continue
        c = grid[y][x] or (BG[nxt] if edge and (x + y) % 2 else BG[band])
        img.putpixel((x, y), hexrgb(c if c.startswith("#") else PAL[c]))

out = Path(sys.argv[1])
img.save(out / "icon-32.png")
rects = []
for y in range(N):
    for x in range(N):
        r, g, b, a = img.getpixel((x, y))
        if a:
            rects.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="#{r:02x}{g:02x}{b:02x}"/>')
(out / "icon.svg").write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {N} {N}" shape-rendering="crispEdges">'
    + "".join(rects) + "</svg>\n")
sheet = Image.new("RGBA", (560, 300), (35, 38, 41, 255))
sheet.paste(Image.new("RGBA", (560, 150), (239, 240, 241, 255)), (0, 150))
for row in range(2):
    x = 16
    for s in (128, 64, 48, 32, 22, 16):
        im = img.resize((s, s), Image.NEAREST if s >= 32 else Image.LANCZOS)
        sheet.alpha_composite(im, (x, row * 150 + (150 - s) // 2)); x += s + 24
sheet.save(out / "icon-preview.png")
