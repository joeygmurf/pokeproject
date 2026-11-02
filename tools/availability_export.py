#!/usr/bin/env python3
"""Build an availability spreadsheet for the areas built so far.

One row per National Dex number, with whether the species can be obtained in
the stretch of the game that currently exists, and where.

  Yes  - catchable in one of the listed areas, or a starter
  Evo  - not catchable, but evolves from something that is
  No   - unobtainable so far

Species data comes from the preprocessed `gSpeciesInfo`, the same approach
`calc_export.py` uses: the real `arm-none-eabi-cpp` runs over the headers, so
`#if P_FAMILY_*` gating and macro-valued fields resolve exactly as they do in
the ROM. Encounters come from `src/data/wild_encounters.json`.

Writes a .xlsx directly (zip + XML); the WSL image has no openpyxl.
"""

import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calc_export import ROOT, preprocess, parse_national_dex, iter_species_blocks  # noqa: E402

# The areas the player can currently reach, in route order, with the label to
# print. Petalburg Woods is excluded deliberately: it is behind Gate A.
AREAS = [
    ("MAP_LITTLEROOT_TOWN", "Littleroot Town"),
    ("MAP_ROUTE101", "Route 101"),
    ("MAP_OLDALE_TOWN", "Oldale Town"),
    ("MAP_ROUTE102", "Route 102"),
    ("MAP_ROUTE103", "Route 103"),
    ("MAP_PETALBURG_CITY", "Petalburg City"),
    ("MAP_ROUTE110", "Route 110"),
    ("MAP_ROUTE117", "Route 117"),
    ("MAP_ROUTE111", "Route 111"),
    ("MAP_ROUTE112", "Route 112"),
    ("MAP_FIERY_PATH", "Fiery Path"),
    ("MAP_ROUTE113", "Route 113"),
]

# json key -> how to label it. Land is the default and goes unlabelled.
METHODS = [
    ("land_mons", ""),
    ("water_mons", "Surf"),
    ("rock_smash_mons", "Rock Smash"),
    ("fishing_mons", "Fishing"),
]

LAST_GEN6_DEX = 721  # Volcanion


def read_starters():
    """The three starters, taking the Emerald side of each IS_FRLG ternary.

    sStarterMon holds GRASS_STARTER/FIRE_STARTER/WATER_STARTER, each defined as
    `(IS_FRLG ? <frlg> : <emerald>)`, so the species names are in the #defines
    rather than the table.
    """
    text = (ROOT / "src/starter_choose.c").read_text(encoding="utf-8")
    starters = re.findall(
        r"#define\s+\w+_STARTER\s+\(IS_FRLG\s*\?\s*SPECIES_[A-Z0-9_]+\s*:\s*(SPECIES_[A-Z0-9_]+)",
        text,
    )
    if len(starters) != 3:
        sys.exit(f"expected 3 starters, parsed {starters}")
    return starters


def read_encounters():
    """species constant -> {area label -> set of method labels}."""
    data = json.loads((ROOT / "src/data/wild_encounters.json").read_text(encoding="utf-8"))
    group = next(g for g in data["wild_encounter_groups"] if g["label"] == "gWildMonHeaders")
    by_map = {}
    for entry in group["encounters"]:
        by_map.setdefault(entry["map"], []).append(entry)

    found = {}
    for map_const, label in AREAS:
        if map_const not in by_map:
            sys.exit(f"no wild data for {map_const} - was it renamed?")
        for entry in by_map[map_const]:
            for key, method in METHODS:
                section = entry.get(key)
                if not section:
                    continue
                for mon in section["mons"]:
                    species = mon["species"]
                    if species == "SPECIES_NONE":
                        continue
                    found.setdefault(species, {}).setdefault(label, set()).add(method)
    return found


def read_species(flat, dex_numbers):
    """constant -> dict(dex, name, evolves_to) for base forms only."""
    name_re = re.compile(r"\.speciesName\s*=\s*_\(\s*\"((?:[^\"\\]|\\.)*)\"")
    dex_re = re.compile(r"\.natDexNum\s*=\s*(NATIONAL_DEX_[A-Z0-9_]+)")
    # cpp expands the EVOLUTION macro, so by this point the field reads
    # `.evolutions = (const struct Evolution[]) { {EVO_LEVEL, 16, SPECIES_X}, ... }`
    # on one line, terminated by a `{ 0xFFFF }` sentinel that holds no species.
    #
    # Do NOT anchor on the entry's closing brace. Conditional evolutions carry a
    # nested `((const struct EvolutionParam[]) { ... })` after the species, so a
    # `[^{}]*\}` tail cannot reach the end and the whole entry is skipped - which
    # silently dropped Typhlosion and every other condition-gated evolution while
    # leaving the plain ones working. Match forward to the species and stop.
    evo_re = re.compile(r"\.evolutions\s*=\s*(.*)")
    target_re = re.compile(r"\{\s*EVO_[A-Z0-9_]+\s*,[^{}]*?(SPECIES_[A-Z0-9_]+)")

    species = {}
    for constant, body in iter_species_blocks(flat):
        dex_const = dex_re.search(body)
        name = name_re.search(body)
        if not dex_const or not name:
            continue
        evolutions = []
        evo = evo_re.search(body)
        if evo:
            evolutions = target_re.findall(evo.group(1))
            # A species that declares evolutions but parses to none means the
            # pattern has lost touch with the data. Loud, not silent.
            if not evolutions and "EVO_" in evo.group(1):
                sys.exit(f"{constant}: .evolutions present but no targets parsed:\n"
                         f"  {evo.group(1)[:300]}")
        species[constant] = {
            "dex": dex_numbers.get(dex_const.group(1), 0),
            "name": name.group(1),
            "evolves_to": evolutions,
        }
    return species


def resolve(species, obtainable):
    """Spread availability along evolution chains. Returns constant -> source."""
    evo_from = {}
    frontier = list(obtainable)
    seen = set(obtainable)
    while frontier:
        constant = frontier.pop()
        for child in species.get(constant, {}).get("evolves_to", []):
            if child in seen or child not in species:
                continue
            seen.add(child)
            evo_from[child] = species[constant]["name"]
            frontier.append(child)
    return evo_from


def column(index):
    letters = ""
    while index >= 0:
        letters = chr(ord("A") + index % 26) + letters
        index = index // 26 - 1
    return letters


def write_xlsx(path, headers, rows):
    """Minimal single-sheet xlsx. Inline strings, so no shared string table."""
    def cell(col, row, value):
        ref = f"{column(col)}{row}"
        if isinstance(value, int):
            return f'<c r="{ref}"><v>{value}</v></c>'
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'

    body = ['<row r="1">' + "".join(cell(c, 1, h) for c, h in enumerate(headers)) + "</row>"]
    for i, row in enumerate(rows, start=2):
        body.append(f'<row r="{i}">' + "".join(cell(c, i, v) for c, v in enumerate(row)) + "</row>")

    widths = "".join(
        f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>'
        for i, w in enumerate((8, 20, 13, 60))
    )
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
        'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f"<cols>{widths}</cols>"
        f'<sheetData>{"".join(body)}</sheetData>'
        f'<autoFilter ref="A1:{column(len(headers)-1)}{len(rows)+1}"/>'
        "</worksheet>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Availability" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.worksheet+xml"/></Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        'relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    )
    book_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        'relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", book_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/availability.xlsx"

    print("Preprocessing species data...")
    flat = preprocess(
        '#include "global.h"\n'
        '#include "constants/species.h"\n'
        '#include "src/data/pokemon/species_info.h"\n'
    )
    species = read_species(flat, parse_national_dex())
    encounters = read_encounters()
    starters = read_starters()

    missing = [s for s in encounters if s not in species]
    if missing:
        print(f"  warning: {len(missing)} encounter species absent from the build: "
              f"{', '.join(sorted(missing)[:6])}")

    obtainable = set(starters) | (set(encounters) & set(species))
    evo_from = resolve(species, obtainable)

    # One row per dex number: keep the lowest-numbered constant, which is the
    # base form. Alternate forms share a dex number and would duplicate rows.
    by_dex = {}
    for constant, info in species.items():
        if not info["dex"]:
            continue
        current = by_dex.get(info["dex"])
        if current is None or len(constant) < len(current):
            by_dex[info["dex"]] = constant

    rows = []
    counts = {"Yes": 0, "Evo": 0, "No": 0}
    for dex in range(1, LAST_GEN6_DEX + 1):
        constant = by_dex.get(dex)
        if constant is None:
            rows.append([dex, "-", "No", "Not in this build"])
            counts["No"] += 1
            continue
        info = species[constant]
        if constant in starters:
            status, where = "Yes", "Starter"
        elif constant in encounters:
            status = "Yes"
            places = []
            for _, label in AREAS:
                methods = encounters[constant].get(label)
                if not methods:
                    continue
                extra = sorted(m for m in methods if m)
                places.append(f"{label} ({', '.join(extra)})" if extra else label)
            where = ", ".join(places)
        elif constant in evo_from:
            status, where = "Evo", f"Evolves from {evo_from[constant]}"
        else:
            status, where = "No", ""
        counts[status] += 1
        rows.append([dex, info["name"], status, where])

    # Later-gen evolutions of Gen 1-6 families are in this build and obtainable,
    # but sit above #721, so they would otherwise be invisible here.
    extras = sorted(
        (d, c) for d, c in by_dex.items()
        if d > LAST_GEN6_DEX and (c in obtainable or c in evo_from)
    )
    if extras:
        rows.append(["", "", "", ""])
        rows.append(["", "Past Gen 6 (later evolutions of Gen 1-6 families)", "", ""])
        for dex, constant in extras:
            where = (f"Evolves from {evo_from[constant]}" if constant in evo_from else "Starter")
            rows.append([dex, species[constant]["name"], "Evo", where])

    write_xlsx(out, ["Dex", "Pokemon", "Available", "Location"], rows)
    print(f"Wrote {out}")
    print(f"  Yes {counts['Yes']}  Evo {counts['Evo']}  No {counts['No']}"
          f"  (+{len(extras)} past #721)")


if __name__ == "__main__":
    main()
