#!/usr/bin/env python3
"""Export this hack's data for hzla's Dynamic Calc (the `decomp` fork).

Produces a `backup_data` bundle in the schema that fork expects:

    var backup_data = {
      "title": ...,
      "poks":           { "<Showdown name>": { name, num, bs, types, abilities,
                                               weightkg, heightm, learnset_info } },
      "formatted_sets": { "<Showdown name>": { "Lvl <n> <label>": { ... } } },
      "species_indices": { "<index>": "<Showdown name>" }
    }

`poks` is phase 1 (species), `formatted_sets` is phase 2 (trainers).
`species_indices` is for a save reader: saves store species by numeric id, and
this hack compiles Gen 7-9 families out, so our ids match neither vanilla nor
any other hack. It has to come from our own build.

WHY THE C PREPROCESSOR
----------------------
The species data is not regex-parseable. Entries sit behind `#if P_FAMILY_*`
(whole generations are compiled out here) and fields behind `#if
P_UPDATED_EXP_YIELDS >= GEN_8`-style branches. Text-scraping the headers picks
arbitrary branches and happily exports Pokemon that are not in the game.

So we run the real `arm-none-eabi-cpp` over a stub with the project's include
path, exactly as the build does, and parse the flattened result. If this script
and the ROM ever disagree, the preprocessor is the thing they share.

Usage:
    python3 tools/calc_export.py --out build/calc
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CPP = "arm-none-eabi-cpp"
CPP_FLAGS = [
    "-iquote", "include", "-I", "include", "-I", ".",
    "-Wno-trigraphs", "-DMODERN=1", "-DTESTING=0", "-DEMERALD", "-std=gnu17",
]

# Showdown stat keys, in the order the calc's `bs` dict wants them.
STAT_KEYS = ("hp", "at", "df", "sp", "sa", "sd")


def preprocess(source: str) -> str:
    """Run the real preprocessor over `source` and return the flattened text."""
    proc = subprocess.run(
        [CPP, *CPP_FLAGS, "-"],
        input=source, capture_output=True, text=True, cwd=ROOT,
    )
    if proc.returncode != 0:
        sys.exit(f"{CPP} failed:\n{proc.stderr[:4000]}")
    return proc.stdout


def constant_to_name(constant: str, prefix: str) -> str:
    """ABILITY_SWIFT_SWIM -> 'Swift Swim'. A fallback only.

    Real display names are read out of the data files where possible, because
    they already carry the punctuation Showdown expects ("U-turn", "King's
    Shield") which this cannot reconstruct.
    """
    body = constant[len(prefix):] if constant.startswith(prefix) else constant
    return " ".join(part.capitalize() for part in body.split("_") if part)


_C_EXPR_SAFE = re.compile(r"^[0-9\s()?:<>=!&|+\-*/%]+$")


def c_ternary_to_python(text: str) -> str:
    """Rewrite C `cond ? a : b` as Python `(a) if (cond) else (b)`.

    Done by scanning for the `?` and its matching `:` at paren depth zero, so
    parenthesised and nested ternaries survive. A plain regex gets
    `(8 >= 1 ? 100 : 85)` wrong because it cannot tell which `:` belongs to
    which `?`.
    """
    text = text.strip()
    # `(8 >= 1 ? 100 : 85)` hides its `?` at depth 1; peel redundant wrapping
    # parens so the scan below can see it.
    while text.startswith("(") and text.endswith(")"):
        depth = 0
        for i, char in enumerate(text):
            depth += (char == "(") - (char == ")")
            if depth == 0 and i < len(text) - 1:
                break
        else:
            text = text[1:-1].strip()
            continue
        break

    depth, question = 0, -1
    for i, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "?" and depth == 0:
            question = i
            break
    if question == -1:
        return text

    depth = pending = 0
    colon = -1
    for i in range(question + 1, len(text)):
        char = text[i]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and char == "?":
            pending += 1
        elif depth == 0 and char == ":":
            if pending:
                pending -= 1
            else:
                colon = i
                break
    if colon == -1:
        raise ValueError(f"unbalanced ternary: {text!r}")

    cond = c_ternary_to_python(text[:question].strip())
    on_true = c_ternary_to_python(text[question + 1:colon].strip())
    on_false = c_ternary_to_python(text[colon + 1:].strip())
    return f"(({on_true}) if ({cond}) else ({on_false}))"


def eval_c_expr(text: str, field: str):
    """Evaluate the integer expression cpp left behind for a field.

    Several stats are written as `P_UPDATED_STATS >= GEN_6 ? 80 : 70`. The
    preprocessor substitutes the constants but does NOT fold the arithmetic, so
    the value arrives as `8 >= 6 ? 80 : 70`. Taking the first integer out of
    that yields 8 - a plausible-looking number that is simply wrong, which is
    exactly the kind of error nobody notices. 173 species hit this.
    """
    text = text.strip().rstrip(",").strip()
    if text.isdigit():
        return int(text)
    if not _C_EXPR_SAFE.match(text):
        raise ValueError(f"unparseable {field}: {text!r}")
    python = c_ternary_to_python(text)
    # C logical operators have no Python spelling. Mask `!=` first so the `!`
    # rewrite cannot corrupt it.
    python = python.replace("!=", "\x00")
    python = python.replace("||", " or ").replace("&&", " and ").replace("!", " not ")
    python = python.replace("\x00", "!=")
    try:
        return int(eval(python, {"__builtins__": {}}, {}))
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as data
        raise ValueError(f"unparseable {field}: {text!r} ({exc})") from exc


def parse_national_dex() -> dict:
    """NATIONAL_DEX_* -> number, read from the enum's declaration order."""
    text = (ROOT / "include/constants/pokedex.h").read_text(encoding="utf-8")
    # The enum opens with NATIONAL_DEX_NONE = 0 and increments implicitly.
    names = re.findall(r"^\s*(NATIONAL_DEX_[A-Z0-9_]+),", text, re.M)
    return {name: i for i, name in enumerate(names)}


def parse_names(path: str, table_open: str, const_prefix: str) -> dict:
    """Pull `.name = ...("Display")` out of a data table, keyed by constant."""
    text = (ROOT / path).read_text(encoding="utf-8")
    start = text.index(table_open)
    out = {}
    pattern = re.compile(
        r"\[(" + const_prefix + r"[A-Z0-9_]+)\]\s*=\s*\{(.*?)\n    \},",
        re.S,
    )
    name_pattern = re.compile(r"\.name\s*=\s*(?:COMPOUND_STRING|_)\(\s*\"((?:[^\"\\]|\\.)*)\"")
    for match in pattern.finditer(text, start):
        name = name_pattern.search(match.group(2))
        if name:
            out[match.group(1)] = name.group(1)
    return out


def iter_species_blocks(flat: str):
    """Yield (constant, body) for every `[SPECIES_X] = { ... }` entry.

    Brace-matched rather than regex-terminated. An earlier version closed each
    block on the first `\\n    },` and SPECIES_GENESECT - whose Drive forms nest
    deeply - swallowed the 100-odd entries that followed it, silently dropping
    Chespin among others. Counting braces cannot drift like that.
    """
    for match in re.finditer(r"\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*", flat):
        start = flat.find("{", match.end())
        if start == -1:
            continue
        depth, i, n = 0, start, len(flat)
        while i < n:
            char = flat[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        yield match.group(1), flat[start + 1:i]


def form_suffix(constant: str, base_constant: str) -> str:
    """SPECIES_DEOXYS_ATTACK + SPECIES_DEOXYS -> 'Attack'."""
    tail = constant[len(base_constant):].strip("_")
    # "SANDY_CLOAK" -> "Sandy"; Showdown drops these descriptive tails.
    parts = [p for p in tail.split("_") if p and p not in ("CLOAK", "FORM", "FORME", "MODE", "SIZE")]
    return "-".join(p.capitalize() for p in parts)


def parse_species(flat: str, dex_numbers: dict, ability_names: dict) -> tuple:
    """Parse the flattened gSpeciesInfo into calc `poks` entries.

    Returns (poks, learnset_symbol_by_species, species_order).
    """
    poks = {}
    learnset_symbol = {}
    order = []
    base_constant_for = {}  # display name -> the constant of its base form

    for constant, body in iter_species_blocks(flat):

        stats = {}
        for key, field in zip(
            STAT_KEYS,
            ("baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack", "baseSpDefense"),
        ):
            found = re.search(r"\.%s\s*=\s*([^,\n]+)" % field, body)
            if not found:
                break
            stats[key] = eval_c_expr(found.group(1), f"{constant}.{field}")
        if len(stats) != len(STAT_KEYS):
            continue  # Not a real species entry (SPECIES_NONE, SPECIES_EGG...).

        display = re.search(r"\.speciesName\s*=\s*(?:COMPOUND_STRING|_)\(\s*\"((?:[^\"\\]|\\.)*)\"", body)
        name = display.group(1) if display else constant_to_name(constant, "SPECIES_")

        types_found = re.search(r"\.types\s*=\s*\{\s*(TYPE_[A-Z_]+)\s*,\s*(TYPE_[A-Z_]+)\s*\}", body)
        types = []
        if types_found:
            for raw in types_found.groups():
                pretty = constant_to_name(raw, "TYPE_")
                if pretty not in types:
                    types.append(pretty)

        abilities = []
        abil_found = re.search(r"\.abilities\s*=\s*\{([^}]*)\}", body)
        if abil_found:
            for raw in re.findall(r"ABILITY_[A-Z0-9_]+", abil_found.group(1)):
                if raw == "ABILITY_NONE":
                    continue
                pretty = ability_names.get(raw) or constant_to_name(raw, "ABILITY_")
                if pretty not in abilities:
                    abilities.append(pretty)

        dex_const = re.search(r"\.natDexNum\s*=\s*(NATIONAL_DEX_[A-Z0-9_]+)", body)
        num = dex_numbers.get(dex_const.group(1), 0) if dex_const else 0

        # `.height`/`.weight` also appear inside the nested overworldData blob,
        # so anchor to the top-level indent to get the species' own values.
        height = re.search(r"\n        \.height\s*=\s*([^,\n]+)", body)
        weight = re.search(r"\n        \.weight\s*=\s*([^,\n]+)", body)

        # Forms share a speciesName ("Deoxys" for all four), so a second entry
        # under the same display name is an alternate form. Name it from the
        # constant the way Showdown does: Deoxys-Attack, Rotom-Frost.
        base_name = name
        forme = None
        if name in poks:
            forme = form_suffix(constant, base_constant_for.get(name, constant))
            if not forme:
                continue  # A cosmetic duplicate with nothing to distinguish it.
            name = f"{base_name}-{forme}"
            if name in poks:
                continue
        else:
            base_constant_for[name] = constant

        learnset = re.search(r"\.levelUpLearnset\s*=\s*(s\w+)", body)
        if learnset:
            learnset_symbol[name] = learnset.group(1)

        poks[name] = {
            "name": name,
            "num": num,
            "bs": stats,
            "types": types,
            # The calc reads abilities as an index-keyed object, not an array -
            # matching the existing backups in that fork.
            "abilities": {str(i): a for i, a in enumerate(abilities)},
            "weightkg": (eval_c_expr(weight.group(1), f"{constant}.weight") / 10) if weight else 0,
            "heightm": (eval_c_expr(height.group(1), f"{constant}.height") / 10) if height else 0,
            "learnset_info": {"learnset": [], "tms": [], "tutors": [], "eggMoves": []},
        }
        if forme:
            poks[name]["baseSpecies"] = base_name
            poks[name]["forme"] = forme
        order.append((constant, name))

    return poks, learnset_symbol, order


def parse_learnsets(flat: str, move_names: dict) -> dict:
    """symbol -> [[level, 'Move Name'], ...] from the flattened learnset data."""
    out = {}
    block = re.compile(
        r"static const struct LevelUpMove (s\w+LevelUpLearnset)\[\]\s*=\s*\{(.*?)\n\};",
        re.S,
    )
    # The preprocessor expands LEVEL_UP_MOVE(0, MOVE_MUDDY_WATER) into
    # `{.move = MOVE_MUDDY_WATER, .level = 0}` - note the fields swap order, so
    # match on the designators rather than on position.
    pair = re.compile(r"\{\s*\.move\s*=\s*(MOVE_[A-Z0-9_]+)\s*,\s*\.level\s*=\s*(\d+)\s*\}")
    for match in block.finditer(flat):
        moves = []
        for move, level in pair.findall(match.group(2)):
            pretty = move_names.get(move) or constant_to_name(move, "MOVE_")
            moves.append([int(level), pretty])
        out[match.group(1)] = moves
    return out


def parse_moves(flat: str) -> dict:
    """Parse the flattened gMovesInfo into the calc's `moves` table.

    Same ternary problem as the species stats: `.power` is routinely written
    `B_UPDATED_MOVE_DATA >= GEN_6 ? 90 : 95`, so every field goes through
    eval_c_expr rather than a bare integer match.
    """
    categories = {
        "DAMAGE_CATEGORY_PHYSICAL": "Physical",
        "DAMAGE_CATEGORY_SPECIAL": "Special",
        "DAMAGE_CATEGORY_STATUS": "Status",
    }
    out = {}
    for constant, body in iter_named_blocks(flat, "MOVE_"):
        name = re.search(r"\.name\s*=\s*(?:COMPOUND_STRING|_)\(\s*\"((?:[^\"\\]|\\.)*)\"", body)
        if not name:
            continue
        move_type = re.search(r"\.type\s*=\s*(TYPE_[A-Z_]+)", body)
        category = re.search(r"\.category\s*=\s*(DAMAGE_CATEGORY_[A-Z]+)", body)

        def number(field, default=0):
            found = re.search(r"\.%s\s*=\s*([^,\n]+)" % field, body)
            if not found:
                return default
            try:
                return eval_c_expr(found.group(1), f"{constant}.{field}")
            except ValueError:
                return default

        out[name.group(1)] = {
            "basePower": number("power"),
            "type": constant_to_name(move_type.group(1), "TYPE_") if move_type else "Normal",
            "category": categories.get(category.group(1), "Status") if category else "Status",
            "pp": number("pp", 5),
            "accuracy": number("accuracy", 100),
            "priority": number("priority"),
        }
    return out


def iter_named_blocks(flat: str, prefix: str):
    """Yield (constant, body) for `[PREFIX_X] = { ... }` entries, brace-matched."""
    for match in re.finditer(r"\[(" + prefix + r"[A-Z0-9_]+)\]\s*=\s*", flat):
        start = flat.find("{", match.end())
        if start == -1:
            continue
        depth, i, n = 0, start, len(flat)
        while i < n:
            if flat[i] == "{":
                depth += 1
            elif flat[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        yield match.group(1), flat[start + 1:i]


def natural_moveset(learnset, level):
    """The moveset the game gives a trainer mon with no explicit moves.

    GiveMonInitialMoveset walks the learnset in order and keeps the last four
    moves learnable at or below the mon's level.
    """
    known = []
    for lvl, move in learnset:
        if lvl > level:
            break
        if move in known:
            known.remove(move)
        known.append(move)
    return known[-4:]


def parse_trainers(poks, learnsets, learnset_symbol):
    """Parse trainers.party into the calc's `formatted_sets`."""
    text = (ROOT / "src/data/trainers.party").read_text(encoding="utf-8")
    sets = {}
    unknown = set()

    # trainers.party is hand-written, so its capitalisation and punctuation
    # drift from the exported names ("Burmy-trash" vs "Burmy-Trash"). Match on
    # a normalised key and fall back to the base form.
    def normalise(value):
        return re.sub(r"[^a-z0-9]", "", value.lower())

    by_norm = {normalise(k): k for k in poks}

    def resolve(value):
        hit = by_norm.get(normalise(value))
        if hit:
            return hit
        base = value.split("-")[0]
        return by_norm.get(normalise(base))

    # Entries start at `=== TRAINER_X ===`; everything before the first one is
    # the file's own documentation header.
    chunks = re.split(r"^=== (TRAINER_[A-Z0-9_]+) ===$", text, flags=re.M)[1:]

    for tr_id, (constant, body) in enumerate(zip(chunks[0::2], chunks[1::2])):
        header, _, party = body.partition("\n\n")

        def field(key, default=""):
            found = re.search(r"^%s:\s*(.+)$" % re.escape(key), header, re.M)
            return found.group(1).strip() if found else default

        name = field("Name", constant)
        cls = field("Class", "")
        label = re.sub(r"[\[\]()]", "", f"{cls} {name} #{tr_id}").strip()

        for slot, mon_block in enumerate(b for b in party.split("\n\n") if b.strip()):
            lines = [l.rstrip() for l in mon_block.strip().split("\n") if l.strip()]
            if not lines:
                continue

            # Species line: "Nickname (Species) @ Item", "Species @ Item", "Species"
            head = lines[0]
            item = None
            if " @ " in head:
                head, _, item = head.partition(" @ ")
                item = item.strip()
            paren = re.search(r"\(([^)]+)\)\s*$", head.strip())
            species = paren.group(1).strip() if paren else head.strip()
            species = re.sub(r"\s*\((?:M|F)\)\s*$", "", species).strip()

            resolved = resolve(species)
            if not resolved:
                unknown.add(species)
                continue
            species = resolved

            def mon_field(key, default=None):
                for line in lines[1:]:
                    if line.startswith(key + ":"):
                        return line.split(":", 1)[1].strip()
                return default

            level = int(mon_field("Level", "1"))
            moves = [l[2:].strip() for l in lines[1:] if l.startswith("- ")]
            if not moves:
                symbol = learnset_symbol.get(species)
                moves = natural_moveset(learnsets.get(symbol, []), level)

            def stat_spread(raw, default):
                spread = {k: default for k in ("hp", "atk", "def", "spa", "spd", "spe")}
                if raw:
                    for value, stat in re.findall(r"(\d+)\s*(HP|Atk|Def|SpA|SpD|Spe)", raw):
                        spread[stat.lower()] = int(value)
                return spread

            entry = {
                "level": level,
                "nature": mon_field("Nature", "Hardy"),
                "ability": mon_field("Ability", poks[species]["abilities"].get("0", "")),
                "moves": moves,
                "evs": stat_spread(mon_field("EVs"), 0),
                "ivs": stat_spread(mon_field("IVs"), 31),
                "tr_id": tr_id,
                "sub_index": slot,
            }
            if item:
                entry["item"] = item
            if field("Double Battle", "No").lower().startswith("y"):
                entry["battle_type"] = "Doubles"

            per_species = sets.setdefault(species, {})
            key = f"Lvl {level} {label}"
            dupe = 0
            while key in per_species:
                dupe += 1
                key = f"Lvl {level} {label}*{dupe}"
            per_species[key] = entry

    return sets, unknown


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="build/calc", help="output directory")
    ap.add_argument("--title", default="PokeProject", help="calc title for this data source")
    ap.add_argument("--slug", default="pokeproject", help="output file basename")
    args = ap.parse_args()

    out_dir = (ROOT / args.out) if not Path(args.out).is_absolute() else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Preprocessing species data...")
    species_flat = preprocess(
        '#include "global.h"\n'
        '#include "constants/species.h"\n'
        '#include "src/data/pokemon/species_info.h"\n'
    )
    print("Preprocessing level-up learnsets...")
    learnset_flat = preprocess(
        '#include "global.h"\n'
        '#include "src/data/pokemon/level_up_learnsets/gen_9.h"\n'
    )

    dex_numbers = parse_national_dex()
    move_names = parse_names("src/data/moves_info.h", "gMovesInfo", "MOVE_")
    ability_names = parse_names("src/data/abilities.h", "gAbilitiesInfo", "ABILITY_")
    print(f"  {len(move_names)} move names, {len(ability_names)} ability names")

    poks, learnset_symbol, order = parse_species(species_flat, dex_numbers, ability_names)
    learnsets = parse_learnsets(learnset_flat, move_names)
    print(f"  {len(poks)} species, {len(learnsets)} learnsets")

    for name, entry in poks.items():
        symbol = learnset_symbol.get(name)
        entry["learnset_info"]["learnset"] = learnsets.get(symbol, [])

    sets, unknown = parse_trainers(poks, learnsets, learnset_symbol)
    total_sets = sum(len(v) for v in sets.values())
    print(f"  {len(sets)} species with sets, {total_sets} trainer sets")
    if unknown:
        print(f"  WARNING: {len(unknown)} species in trainers.party not in the export:")
        for name in sorted(unknown)[:20]:
            print(f"    {name}")

    print("Preprocessing move data...")
    moves_flat = preprocess('#include "global.h"\n#include "src/data/moves_info.h"\n')
    moves = parse_moves(moves_flat)
    print(f"  {len(moves)} moves")

    bundle = {
        "title": args.title,
        "poks": poks,
        "moves": moves,
        "formatted_sets": sets,
        "species_indices": {str(i): name for i, (_, name) in enumerate(order)},
    }

    # The calc wants a prev/next chain so its trainer previews can step through
    # the game. Default to trainer record order; a story order would have to be
    # curated by hand.
    used_ids = sorted({entry["tr_id"] for species in sets.values() for entry in species.values()})
    orders = {}
    for i, tr_id in enumerate(used_ids):
        orders[str(tr_id)] = {
            "id": tr_id,
            "next": used_ids[i + 1] if i + 1 < len(used_ids) else used_ids[0],
            "prev": used_ids[i - 1] if i else used_ids[-1],
        }
    order_path = out_dir / f"{args.slug}.order.js"
    order_path.write_text(
        "trainerOrders = " + json.dumps(orders, indent=2) + ";\n", encoding="utf-8"
    )

    json_path = out_dir / f"{args.slug}.json"
    js_path = out_dir / f"{args.slug}.js"
    json_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    js_path.write_text(
        "var backup_data = " + json.dumps(bundle, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {json_path}, {js_path} and {order_path}")


if __name__ == "__main__":
    main()
