#!/usr/bin/env python3
"""Render a decomp map as an annotated ASCII grid.

    python3 tools/mapview.py Route102
    python3 tools/mapview.py Route102 --range 14,0,34,12
    python3 tools/mapview.py Route102 --ids          # show metatile ids instead

Shows collision, tall grass, ledges (with jump direction) and NPC positions,
plus a table of object events including each trainer's line of sight.
Read-only - it never writes to the project.
"""
import argparse
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JUMP_ARROW = {
    "EAST": ">", "WEST": "<", "NORTH": "^", "SOUTH": "v",
    "NORTHEAST": "/", "NORTHWEST": "\\", "SOUTHEAST": "\\", "SOUTHWEST": "/",
}
FACING = {
    "MOVEMENT_TYPE_FACE_UP": (0, -1),
    "MOVEMENT_TYPE_FACE_DOWN": (0, 1),
    "MOVEMENT_TYPE_FACE_LEFT": (-1, 0),
    "MOVEMENT_TYPE_FACE_RIGHT": (1, 0),
}


def behavior_names():
    """Map metatile-behavior id -> MB_ name, by parsing the enum in order."""
    path = os.path.join(ROOT, "include/constants/metatile_behaviors.h")
    text = open(path, encoding="utf-8").read()
    body = text[text.index("{"):]
    names = [n.strip() for n in re.findall(r"^\s*(MB_[A-Z0-9_]+)\s*(?:=\s*[^,]+)?,", body, re.M)]
    return {i: n for i, n in enumerate(names)}


def tileset_dir(symbol):
    """gTileset_FooBar -> the data/tilesets/*/foo_bar directory."""
    name = symbol.replace("gTileset_", "")
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    for kind in ("primary", "secondary"):
        path = os.path.join(ROOT, "data/tilesets", kind, snake)
        if os.path.isdir(path):
            return path
    return None


def load_attributes(symbol):
    """metatile index -> behavior id for one tileset."""
    d = tileset_dir(symbol)
    if not d:
        return {}
    path = os.path.join(d, "metatile_attributes.bin")
    if not os.path.exists(path):
        return {}
    raw = open(path, "rb").read()
    return {i: struct.unpack_from("<H", raw, 2 * i)[0] & 0xFF for i in range(len(raw) // 2)}


def load_map(map_name):
    map_json = os.path.join(ROOT, "data/maps", map_name, "map.json")
    if not os.path.exists(map_json):
        sys.exit(f"no such map: {map_json}")
    mapdata = json.load(open(map_json, encoding="utf-8"))

    layouts = json.load(open(os.path.join(ROOT, "data/layouts/layouts.json"), encoding="utf-8"))
    layout = next((l for l in layouts["layouts"] if l and l.get("id") == mapdata["layout"]), None)
    if layout is None:
        sys.exit(f"layout {mapdata['layout']} not found")

    blocks = open(os.path.join(ROOT, layout["blockdata_filepath"]), "rb").read()
    return mapdata, layout, blocks


# Primary tilesets own metatiles 0..511; secondary ones start at 512.
NUM_METATILES_IN_PRIMARY = 512


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map", help="map folder name, e.g. Route102")
    ap.add_argument("--range", help="x0,y0,x1,y1 window to show")
    ap.add_argument("--ids", action="store_true", help="print metatile ids instead of symbols")
    args = ap.parse_args()

    mapdata, layout, blocks = load_map(args.map)
    W, H = layout["width"], layout["height"]
    behaviors = behavior_names()
    primary = load_attributes(layout["primary_tileset"])
    secondary = load_attributes(layout["secondary_tileset"])

    def block(x, y):
        return struct.unpack_from("<H", blocks, 2 * (y * W + x))[0]

    def metatile(x, y):
        return block(x, y) & 0x3FF

    def collision(x, y):
        return (block(x, y) >> 10) & 3

    def behavior(x, y):
        m = metatile(x, y)
        if m < NUM_METATILES_IN_PRIMARY:
            return behaviors.get(primary.get(m, 0), "")
        return behaviors.get(secondary.get(m - NUM_METATILES_IN_PRIMARY, 0), "")

    npcs = {}
    for i, o in enumerate(mapdata.get("object_events", [])):
        npcs[(o["x"], o["y"])] = (i, o)

    x0, y0, x1, y1 = 0, 0, W - 1, H - 1
    if args.range:
        x0, y0, x1, y1 = (int(v) for v in args.range.split(","))
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(W - 1, x1), min(H - 1, y1)

    def symbol(x, y):
        if (x, y) in npcs:
            return str(npcs[(x, y)][0])[-1]
        b = behavior(x, y)
        if b.startswith("MB_JUMP_"):
            return JUMP_ARROW.get(b.replace("MB_JUMP_", ""), "L")
        if collision(x, y):
            return "#"
        if "TALL_GRASS" in b or "LONG_GRASS" in b:
            return "g"
        if "WATER" in b or "DEEP" in b:
            return "~"
        if "DOOR" in b or "WARP" in b or "STAIRS" in b or "LADDER" in b:
            return "D"
        return "."

    print(f"{args.map}  {W}x{H}  layout={layout['id']}")
    print(f"  tilesets: {layout['primary_tileset']} + {layout['secondary_tileset']}\n")

    if args.ids:
        print("      " + "".join(f"{x:>5}" for x in range(x0, x1 + 1)))
        for y in range(y0, y1 + 1):
            cells = "".join(f"{metatile(x, y):>4X}" + ("*" if collision(x, y) else " ")
                            for x in range(x0, x1 + 1))
            print(f"y{y:>3}  {cells}")
    else:
        if x1 >= 10:
            print("    " + "".join(str(x // 10) for x in range(x0, x1 + 1)))
        print("    " + "".join(str(x % 10) for x in range(x0, x1 + 1)))
        for y in range(y0, y1 + 1):
            print(f"y{y:>2} " + "".join(symbol(x, y) for x in range(x0, x1 + 1)))
        print("\nlegend: # blocked   g tall grass   ~ water   D door/warp   . walkable")
        print("        < > ^ v ledge (arrow = direction you may jump)")
        print("        digit = object event, last digit of its index")

    print("\nobject events:")
    for i, o in enumerate(mapdata.get("object_events", [])):
        line = (f"  [{i}] ({o['x']},{o['y']}) {o['graphics_id']}"
                f"  {o['movement_type']}  range=({o['movement_range_x']},{o['movement_range_y']})")
        if o.get("trainer_type", "TRAINER_TYPE_NONE") != "TRAINER_TYPE_NONE":
            rng = int(o["trainer_sight_or_berry_tree_id"])
            d = FACING.get(o["movement_type"])
            seen = []
            if d:
                for step in range(1, rng + 1):
                    tx, ty = o["x"] + d[0] * step, o["y"] + d[1] * step
                    if not (0 <= tx < W and 0 <= ty < H) or collision(tx, ty):
                        break
                    seen.append((tx, ty))
            line += f"\n        trainer, sight={rng}, sees {seen if d else '(facing varies)'}"
        line += f"\n        script: {o['script']}"
        print(line)


if __name__ == "__main__":
    main()
