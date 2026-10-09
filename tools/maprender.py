#!/usr/bin/env python3
"""Render a decomp map (or part of one) to a PNG, exactly as the game draws it.

    python3 tools/maprender.py Route103 -o /tmp/r103.png
    python3 tools/maprender.py Route103 --range 18,6,52,16 -o /tmp/beach.png --scale 3
    python3 tools/maprender.py Route104 --range 4,66,24,79 -o /tmp/ref.png --scale 3

Composites the real tiles, palettes and metatiles, so what comes out is what
the GBA would show. Read-only; uses only the standard library.
"""
import argparse
import json
import os
import re
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM_TILES_IN_PRIMARY = 512
NUM_PALS_IN_PRIMARY = 6
TILE = 8
MT = 16  # metatile pixel size


# ---------------------------------------------------------------- PNG in/out
def read_png_indexed(path):
    """Minimal PNG reader for the indexed tile sheets (4bpp or 8bpp)."""
    d = open(path, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\x08"[:1] + b"PNG\r\n\x1a\n":
        if d[:8] != bytes([137, 80, 78, 71, 13, 10, 26, 10]):
            sys.exit(f"{path}: not a PNG")
    pos, idat, w = 8, bytearray(), None
    while pos < len(d):
        (ln,) = struct.unpack_from(">I", d, pos)
        typ = d[pos + 4:pos + 8]
        body = d[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bitdepth, colortype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if interlace:
                sys.exit(f"{path}: interlaced PNG not supported")
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln

    raw = zlib.decompress(bytes(idat))
    stride = (w * bitdepth + 7) // 8
    bpp = max(1, bitdepth // 8)
    rows, prev, p = [], bytearray(stride), 0
    for _ in range(h):
        ft = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 1:   line[i] = (line[i] + a) & 0xFF
            elif ft == 2: line[i] = (line[i] + b) & 0xFF
            elif ft == 3: line[i] = (line[i] + ((a + b) >> 1)) & 0xFF
            elif ft == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        prev = line
        if bitdepth == 4:
            row = []
            for byte in line:
                row.append(byte >> 4); row.append(byte & 0xF)
            rows.append(row[:w])
        else:
            rows.append(list(line[:w]))
    return w, h, rows


def write_png_rgb(path, w, h, pixels):
    """pixels: flat bytearray of w*h*3."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += pixels[y * w * 3:(y + 1) * w * 3]

    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    out = bytes([137, 80, 78, 71, 13, 10, 26, 10])
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    out += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    out += chunk(b"IEND", b"")
    open(path, "wb").write(out)


def read_jasc_pal(path):
    lines = open(path, encoding="utf-8").read().split()
    nums = [int(v) for v in lines[3:]]
    return [tuple(nums[i:i + 3]) for i in range(0, len(nums), 3)][:16]


# ------------------------------------------------------------------ tilesets
def tileset_dir(symbol):
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", symbol.replace("gTileset_", "")).lower()
    for kind in ("primary", "secondary"):
        p = os.path.join(ROOT, "data/tilesets", kind, snake)
        if os.path.isdir(p):
            return p
    sys.exit(f"tileset dir not found for {symbol}")


def load_tileset(symbol):
    d = tileset_dir(symbol)
    w, h, idx = read_png_indexed(os.path.join(d, "tiles.png"))
    per_row = w // TILE
    tiles = []
    for t in range((h // TILE) * per_row):
        tx, ty = (t % per_row) * TILE, (t // per_row) * TILE
        tiles.append([row[tx:tx + TILE] for row in idx[ty:ty + TILE]])
    pals = {}
    for f in os.listdir(os.path.join(d, "palettes")):
        if f.endswith(".pal"):
            pals[int(f[:-4])] = read_jasc_pal(os.path.join(d, "palettes", f))
    meta = open(os.path.join(d, "metatiles.bin"), "rb").read()
    return tiles, pals, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--range", help="x0,y0,x1,y1 in tiles")
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--grid", action="store_true", help="overlay a 1px tile grid")
    args = ap.parse_args()

    mj = json.load(open(os.path.join(ROOT, "data/maps", args.map, "map.json"), encoding="utf-8"))
    layouts = json.load(open(os.path.join(ROOT, "data/layouts/layouts.json"), encoding="utf-8"))
    L = next(l for l in layouts["layouts"] if l and l.get("id") == mj["layout"])
    W, H = L["width"], L["height"]
    blocks = open(os.path.join(ROOT, L["blockdata_filepath"]), "rb").read()

    ptiles, ppals, pmeta = load_tileset(L["primary_tileset"])
    stiles, spals, smeta = load_tileset(L["secondary_tileset"])

    def metatile_entries(mid):
        if mid < NUM_TILES_IN_PRIMARY:
            base, blob = mid * MT, pmeta
        else:
            base, blob = (mid - NUM_TILES_IN_PRIMARY) * MT, smeta
        return [struct.unpack_from("<H", blob, base + 2 * i)[0] for i in range(8)]

    def tile_pixels(tid):
        return ptiles[tid] if tid < NUM_TILES_IN_PRIMARY else stiles[tid - NUM_TILES_IN_PRIMARY]

    def palette(pn):
        return (ppals if pn < NUM_PALS_IN_PRIMARY else spals).get(pn, [(255, 0, 255)] * 16)

    x0, y0, x1, y1 = (0, 0, W - 1, H - 1)
    if args.range:
        x0, y0, x1, y1 = (int(v) for v in args.range.split(","))
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(W - 1, x1), min(H - 1, y1)
    cols, rows_n = x1 - x0 + 1, y1 - y0 + 1
    pw, ph = cols * MT, rows_n * MT
    buf = bytearray(pw * ph * 3)

    def put(px, py, rgb):
        if 0 <= px < pw and 0 <= py < ph:
            o = (py * pw + px) * 3
            buf[o:o + 3] = bytes(rgb)

    for my in range(y0, y1 + 1):
        for mx in range(x0, x1 + 1):
            mid = struct.unpack_from("<H", blocks, 2 * (my * W + mx))[0] & 0x3FF
            ox, oy = (mx - x0) * MT, (my - y0) * MT
            for layer in (0, 1):            # bottom first, then top (index 0 = see-through)
                for q in range(4):
                    e = metatile_entries(mid)[layer * 4 + q]
                    tid, xf, yf, pn = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1, (e >> 12) & 0xF
                    pal, tp = palette(pn), tile_pixels(tid)
                    qx, qy = (q % 2) * TILE, (q // 2) * TILE
                    for ty in range(TILE):
                        sy = TILE - 1 - ty if yf else ty
                        for tx in range(TILE):
                            sx = TILE - 1 - tx if xf else tx
                            ci = tp[sy][sx]
                            if layer == 1 and ci == 0:
                                continue
                            put(ox + qx + tx, oy + qy + ty, pal[ci])
            if args.grid:
                for i in range(MT):
                    put(ox + i, oy, (255, 0, 255)); put(ox, oy + i, (255, 0, 255))

    if args.scale > 1:
        s = args.scale
        big = bytearray(pw * s * ph * s * 3)
        for y in range(ph):
            for x in range(pw):
                o = (y * pw + x) * 3
                px = buf[o:o + 3]
                for dy in range(s):
                    row = (y * s + dy) * pw * s
                    for dx in range(s):
                        b = (row + x * s + dx) * 3
                        big[b:b + 3] = px
        buf, pw, ph = big, pw * s, ph * s

    write_png_rgb(args.out, pw, ph, buf)
    print(f"wrote {args.out}  {pw}x{ph}  (tiles x={x0}..{x1} y={y0}..{y1})")


if __name__ == "__main__":
    main()
