# Project Overview

Read this first. It covers what the hack is, how to build and test it, who does
what, and the traps already paid for. The story reorder has its own spec in
[progression.md](progression.md).

---

## 1. What this is

A difficulty hack of Pokémon Emerald built on a fork of RHH's
**pokeemerald-expansion 1.17.2** (`joeygmurf/pokeproject`, branch `master`,
`upstream` → rh-hideout).

**Base level**
- Gen 1–6 Pokémon only, with Gen 9 battle mechanics
- Mega Evolution is the single signature gimmick — Gigantamax and Terastal
  forms are compiled out
- Hard per-milestone level caps, EVs disabled entirely on both sides

**Big goals**, in the order they make sense to build:
1. Difficulty curve — trainer parties, AI flags, level caps *(user-owned)*
2. New rivals
3. New Mega Evolutions *(gated on sprite art)*
4. New gyms *(hardest — badge count is load-bearing across HM gating, Elite
   Four entry, the trainer card and the level-cap list)*

**Plus a story reorder** that makes **Wattson the first gym** — the thing that
separates this from other difficulty hacks. See [progression.md](progression.md).

---

## 2. Division of labour

**The user authors the difficulty curve** — trainer parties, levels, AI flags,
species data, learnsets, and map layout work in Porymap.

**Claude handles code**: engine/C changes, new features and items, event
scripts, map/NPC logic and verification, build and tooling. Don't volunteer to
mass-rewrite trainer parties.

---

## 3. Build and run

Project lives in the **WSL2 Linux filesystem** at `~/decomps/pokeproject`
(never `/mnt/c` — far slower). Ubuntu 26.04, user `joey_murphy`, 16 cores.
Toolchain is modern `arm-none-eabi-gcc`; no agbcc or devkitARM.

```bash
make -j16                 # ~2.5 min cold, seconds for data-only edits
make check                # expansion's battle test suite
make release              # strips debug features for distribution
```

**Playing it.** mGBA cannot reliably write `.sav` files over the
`\\wsl.localhost\` share, so the ROM is copied to
`C:\Users\Joey Murphy\PokeProject-Play\` and launched from there.

```powershell
Copy-Item "\\wsl.localhost\Ubuntu\home\joey_murphy\decomps\pokeproject\pokeemerald.gba" `
          "C:\Users\Joey Murphy\PokeProject-Play\pokeemerald.gba" -Force
```

**Debug menu** is on in non-release builds: hold **R + START** in the overworld
for warps, flag/var editing and instant Pokémon. Essential for testing gates
without replaying.

**Pushing.** `git push` must be run from the user's own VS Code WSL terminal —
Git Credential Manager is a Windows GUI app and cannot prompt when git is
invoked from a non-console context, so it hangs silently instead.

---

## 4. Tooling built for this project

| Tool | What it's for |
|---|---|
| `tools/mapview.py` | ASCII map: collision, grass, ledges with jump arrows, NPCs, and each trainer's computed sight line. Read-only. |
| `tools/maprender.py` | Renders a map region to **PNG using the real tiles/palettes/metatiles**. Use this to *check map edits by looking* rather than inferring from metatile IDs. |
| `tools/porymap_cleanup.py` | Repairs Porymap's partial writes and drops its formatting churn. The Makefile runs `--repair-only` automatically before generating map sources. |

```bash
python3 tools/mapview.py Route103 --range 18,8,52,14
python3 tools/maprender.py Route103 --range 18,8,52,14 --scale 4 -o /tmp/a.png
python3 tools/porymap_cleanup.py --apply      # before committing, to drop churn
```

---

## 5. Working rules

- **Back up and branch before anything substantial.** Tarballs go to
  `~/decomps/backups/`. One feature per branch, merged when verified.
- **Verify map and gate edits with a flood fill**, not by eye: confirm the
  blocker's tile is a genuine single-tile cut point, and that the route is still
  passable (no softlock). Several "obvious" blocking spots turn out to be
  walkable around.
- **Render map edits and look at them** before showing the user.
- **Re-read files before editing** — the user edits the same tree directly.
- **Include a migration branch** when adding a gate, so in-progress saves don't
  regress.
- Object positions are baked into the save for the map you're standing on;
  after moving an NPC, load from a *different* map to see the change.

---

## 6. Traps already paid for

**Vanilla state vars are reused across unrelated story beats.**
`VAR_PETALBURG_CITY_STATE` is 2–3 during the early Wally intro but 4–5 during
the *post-Norman* sequence that hands over HM Surf. Use `VAR_STORY_PROGRESS`
(`include/constants/story_progress.h`) for new gates; milestones are spaced by
10 and gates compare with `>=`.

**Porymap writes over the WSL share can corrupt files.** It has silently lost
one byte near the 8 KB mark in `heal_locations.json` three times — a `},` losing
its comma. It happens whether or not Porymap is running, so "close it first" is
not a fix. The build repairs it automatically now.

**Porymap defaults new objects to `elevation: 0`.** Hoenn ground is elevation 3.
An NPC at 0 does not reliably block the player — it looks fine on the map and
only shows up as "the blocker doesn't block."

**FRLG object sprites collide with Hoenn palettes.** They use the
`OBJ_EVENT_PAL_TAG_NPC_BLUE/RED/GREEN` family, which fights Hoenn's `NPC_1..4`
scheme. Two different palette tags cannot share a `PALSLOT_*`; the loser renders
as **nothing** while still blocking and talking. An invisible-but-functional NPC
on a Hoenn map is almost always this.

**Trees are 2 wide × 3 tall** — a walkable crown row over two blocked body rows.
Never block or unblock individual tiles inside an existing tree; it splits the
crown and renders a half-tree. Place a self-contained tree in open terrain
instead.

**Hoenn shoreline tiling** (derived from ~1,900 sand tiles across maps sharing
`gTileset_General`; Route 104 is the reference beach): sand is only ever `11C`
(water directly above) or `124` fill — **every** edge and corner is carried by
the *water* tiles: `12C` below sand, `123`/`125` sand to E/W, `145`/`146` coast
turns up, `11B`/`11D` coast turns down, `12B`/`12D` outer diagonals. There is no
south-facing sand edge. Avoid 1-tile-tall features; the corner set can't resolve
them.

**`trainerproc` does not validate move legality.** A species can be given a move
it could never learn and the build will accept it silently.

**Upstream bug, worked around:** catching with a **full party** crashed the game
— expansion's Gen 7+ swap menu rendered six copies of the party's first species
and locked up. Ruled out as ours (the whole path is byte-identical to upstream);
symptom points at `BufferBattlePartyOrderBySide` party-index handling, cf.
rh-hideout issue #10893. Never reproduced on demand. `B_CATCH_SWAP_INTO_PARTY`
is set to `GEN_6` in `include/config/battle.h`, so full-party catches go
straight to the PC. Re-enable if upstream fixes it.

---

## 7. Where key things live

| What | Where |
|---|---|
| Feature flags | `include/config/*.h` — most "features" are a flag flip |
| Story spine | `include/constants/story_progress.h` |
| Level caps | `src/caps.c` + `include/config/caps.h` |
| HM → badge gating | `src/field_move.c` (one table) |
| Trainer parties | `src/data/trainers.party` (Showdown syntax, 855 trainers) |
| AI flag composites | `include/constants/battle_ai.h` |
| Wild encounters | `src/data/wild_encounters.json` |
| Species data | `src/data/pokemon/species_info/gen_N_families.h` — named for the *family's* origin gen |
| Learnsets | `src/data/pokemon/level_up_learnsets/gen_9.h` (only this one compiles) |
| Maps | `data/maps/<Map>/` (map.json, scripts.inc) + `data/layouts/<Map>/map.bin` |

**`P_GEN_X_POKEMON` gates by evolutionary family, keyed to the family's *first*
member** — so Gen 1–6 on / 7–9 off still includes later-gen evolutions and
regional forms of those families (Annihilape, Kingambit, Sneasler, Clodsire…).

---

## 8. Current state

**Built and verified:** Gen 1–6 dex with Gen 9 mechanics · level-cap ladder on
milestone flags · EVs disabled · `VAR_STORY_PROGRESS` spine · Route 103 sand
crossing · Gate A (Aqua blockade) · Gate B (Route 103 blocker) · Infinite Candy
key item · L-button field menu (PokéVial + Infinite Repel) · Old Rod moved to
Petalburg · Littleroot and Oldale grass with wild data · Littleroot patch gated
behind owning a Pokémon · starter as a fateful encounter · Roxanne and Tiana
rebuilt · Route 102/103/104 NPC and terrain work.

**Open:**
- **Gate D (Rusturf Tunnel)** — highest risk. Wattson-first means Rock Smash
  arrives first, so the tunnel's rock barrier gates nothing.
- **Gate C (Slateport)** — condition undefined.
- Wally's Mauville scene, Scott dialogue.
- The remaining ~850 trainers *(user-owned)*.
- New rivals, new Megas, new gyms.
- `FLAG_CAP_TBD_AFTER_WATTSON` is a placeholder — the cap holds at 24 after
  Wattson until the next milestone is designed.
