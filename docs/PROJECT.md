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
make check                # expansion's battle test suite (builds ALL species)
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

**Merge before asking for a push.** `git push origin master` pushes whatever
local `master` points at. Work sitting on an unmerged feature branch is simply
not included, and git reports success — "everything up-to-date" — having sent
nothing. This has bitten three times. Fast-forward master *without* checking it
out, so a dirty working tree is untouched:

```bash
git fetch . <feature-branch>:master     # only if master is an ancestor
git rev-list --count origin/master..master   # confirm it moved, THEN ask
```

---

## 4. Tooling built for this project

| Tool | What it's for |
|---|---|
| `tools/mapview.py` | ASCII map: collision, grass, ledges with jump arrows, NPCs, and each trainer's computed sight line. Read-only. |
| `tools/maprender.py` | Renders a map region to **PNG using the real tiles/palettes/metatiles**. Use this to *check map edits by looking* rather than inferring from metatile IDs. |
| `tools/porymap_cleanup.py` | Repairs Porymap's partial writes and drops its formatting churn. The Makefile runs `--repair-only` automatically before generating map sources. |
| `tools/calc_export.py` | Exports this hack's species, moves, trainer parties and save-reader tables for the damage calculator. See §4b. |

**In-game: the `Hack…` debug menu** (R + START, first entry), defined in
`data/scripts/debug_hack.inc` + the tables in `src/debug.c`.

- **Story jump…** moves `VAR_STORY_PROGRESS` and everything riding on it to a
  milestone. Cumulative: the Wattson entry also applies Wally and the rival.
  Deliberately gives no Pokémon or items — stock *Cheat start* and *Give X…*
  already do that, and mixing them makes the state hard to reason about.
- **Warp…** lands a short walk from each custom event, so the trigger still
  has to fire normally. Adding one is two lines; the pattern is commented.

Two entries set state *and* warp: **`Mauville pre-Wattson`** and
**`Verdanturf pre-Wally`**, both landing outside the respective Pokémon Center
at `STORY_RIVAL_ROUTE110` with the Wally errand rewound. They share flags —
talking to the uncle sets nothing, so the two differ only in where you stand.
Both route through `Debug_Hack_Rewind_WallyErrand`, which must clear
`FLAG_HIDE_VERDANTURF_TOWN_WANDAS_HOUSE_WALLY` itself: Mauville's
`ON_TRANSITION` is what normally reveals him, so warping straight to Verdanturf
would find Wanda's House empty and the errand unfinishable.

**AI flags.** Trainer AI is one `AI:` line in `trainers.party`; `trainerproc`
uppercases the slash-separated names and prefixes `AI_FLAG_`. This hack
**removes `SMART_SWITCHING` from the `AI_FLAG_SMART_TRAINER` composite** — it
gates the generic "this matchup is bad, I'm leaving" reads
(`ShouldSwitchIfHasBadOdds`, `ShouldSwitchIfAllScoresBad`) and made every smart
trainer pivot constantly on damage math. What remains only switches for a
concrete reason: Wonder Guard, Truant, no move affects the target, a dead Choice
lock, Perish Song. `SMART_MON_CHOICES` is kept explicitly, because
`SMART_SWITCHING` used to pull it in implicitly and it governs the separate
post-KO send-in decision. A `AI_FLAG_PIVOT_TRAINER` TODO marks where to add it
back for trainers that *should* pivot. **This edits an upstream macro, so expect
a merge conflict there.**

Other stock debug entries worth knowing: **Party… → Set Party** loads the
party from `src/data/debug_trainers.party` (Showdown syntax, same as
`trainers.party`), and **Start Debug Battle** loads both sides from that file
and starts the fight — the fastest way to iterate a trainer's party.
**PC/Bag… → Fill… → Fill Boxes: Wild Mons…** (ours) stores one of every species
that appears anywhere in `wild_encounters.json` — all times of day, all five
encounter areas — at the current level cap or a fixed 20/30/50/100, with random
personality and IVs. ~288 species, so it fills about ten boxes. It walks the
compiled `gWildMonHeaders`, not the JSON, so it cannot disagree with the ROM.
**Flags & Vars… → All badges** is the quickest obedience override, because
`FLAG_BADGE08_GET` short-circuits the check outright; *Trainer See OFF*,
*Collision OFF* and *Encounter OFF* live in the same submenu.

```bash
python3 tools/mapview.py Route103 --range 18,8,52,14
python3 tools/maprender.py Route103 --range 18,8,52,14 --scale 4 -o /tmp/a.png
python3 tools/porymap_cleanup.py --apply      # before committing, to drop churn
```

---

---

## 4b. Damage calculator

A local instance of **hzla's Dynamic Calc** (the `decomp` fork) runs against this
hack's own data — species, trainer parties and `.sav` import. The calculator
lives **outside this repo**, cloned at `~/decomps/dynamic-calc`; only the
exporter is ours.

```bash
python3 tools/calc_export.py --install        # regenerate + copy into the calc
cd ~/decomps/dynamic-calc && python3 -m http.server 8777
```

Then open, and **hard-refresh (Ctrl+Shift+R)** after every re-export — the data
file is served without a cache-busting query, so a normal reload serves a stale
2.5 MB bundle and it looks like the export failed:

```
http://localhost:8777/index.html?data=pokeproject&dmgGen=8&gen=8&types=6&noSwitch=1&evs=0
```

`--install` places three files; they must move together, because updating the
data without the save constants leaves the save reader resolving species
against a stale table, which **misreports Pokémon rather than failing**.

**The exporter preprocesses rather than scrapes.** Species data hides behind
`#if P_FAMILY_*`, fields behind `#if P_UPDATED_STATS` branches, and some values
are bare macros (`CHARIZARD_SP_ATK`, `MAGNEMITE_FAMILY_TYPE2`). It runs the real
`arm-none-eabi-cpp` and parses the flattened output, so it cannot disagree with
the ROM. Four bugs during its construction all produced *plausible but wrong*
output — a stat of `8` read out of `8 >= 6 ? 80 : 70`, empty learnsets, a
species block swallowing the hundred after it, and typeless Pokémon making
every damage roll `NaN`. It now fails loudly instead of guessing.

**Four edits were made to the calc clone** (not version-controlled by us): a
catalog entry, a title→backup mapping, a settings branch forcing
`sourceType = "full"`, and widening the save reader's `TITLE.includes("Imperium")`
gate. `sourceType` is the subtle one — the default `onlyTrainers` loads trainer
sets but **silently ignores species and move data**, so the calc appears to work
while using the vanilla dex. Fork the repo before investing further.

Known gap: `tms`, `tutors` and `eggMoves` are empty — level-up learnsets only.

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

A **different** shape has since appeared: the file losing its whole tail (66
lines, including the closing bracket), which `porymap_cleanup.py` does **not**
repair. Symptom is `JSONPROC_ERROR: ... unexpected end of input`. The file is
tracked, so `git checkout -- src/data/heal_locations.json` fixes it.

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

**The camera is 15x10 tiles with the player centred**, so visible x runs
`playerX-7 .. playerX+7`. Work this out *before* choosing which way a cutscene
NPC walks off: "off screen" means out of that window, not the map edge. On
Route 110 a westward exit was impossible because the player stood at x=3 and
the map stopped at x=0 — the fix was to move the trigger column east, not to
add more steps.

**`include/constants/map_event_ids.h` is generated and gitignored.** A
hand-written `LOCALID_*` there survives until the next `mapjson` run, then
vanishes. Declare it as a `local_id` field on the object in `map.json`; the
define is emitted from that.

**`make check` builds every species; the normal build does not.** With Gen 7-9
families compiled out, a typo'd constant in their data is completely silent
until the test suite runs. `MOVE_ACCELROCK` (for `MOVE_ACCELEROCK`) sat
committed in four Rockruff/Lycanroc learnsets exactly this way.

**Flood fills must exclude water.** Water has collision 0, so a terrain-only
fill walks across it and reports leaks that do not exist for a player without
Surf. Check the metatile behaviour for `WATER`/`DEEP` as well as collision, and
remember NPC-occupied tiles block too — the Route 110 cut point only holds
because the Team Aqua grunts stand on (8..11, 73).

**Obedience keys off badge numbers too, and the reorder broke it.**
`GetAttackerObedienceForAction` (`src/battle_util.c`) derives its level ceiling
from badges: 10 with none, 20 at badge 1, 30 at badge 2. Wattson being first
means the player holds **no badge at all** until Mauville while the cap is
already 19, so a Pokémon *caught at 19* disobeyed — while one caught at 5 and
raised to 19 did not, because the check reads **met level**, not current level.
Fixed by holding `B_OBEDIENCE_MECHANICS` at `GEN_7`, which restricts obedience
to traded Pokémon and leaves `src/caps.c` the sole authority on levels.

This is the same shape as the `sLevelCapFlagMap` problem, in a second system.
**Anything keyed to badge *number* rather than a specific flag is suspect** —
`sEvCapFlagMap` has the identical flaw and is only dormant because
`B_EV_CAP_TYPE` is `EV_CAP_NO_GAIN`.

**`AI_FLAG_SMART_TERA` grants Terastal, despite what its comment says.**
`GenerateMonFromTrainerMon` stamps `TYPE_MYSTERY` — the sentinel that denies the
gimmick — only on trainers *lacking* that flag. With it, the mon keeps
`TYPE_NONE`, `MON_DATA_TERA_TYPE` then derives a real type from the species, and
the gate opens. Since `SMART_TERA` is bundled inside `AI_FLAG_SMART_TRAINER`,
moving trainers onto that composite silently enabled Terastal everywhere. The
sentinel is now unconditional in `src/trainer_util.c`: trainers Terastallize
only with an explicit `Tera Type:` line.

**Fishing rod slots live in two places that drift apart silently.** The rods
are **3 old / 3 good / 5 super** here, not vanilla's 2/3/5. Porymap edits the
`groups` arrays in `src/data/wild_encounters.json`, which *generate* the
`ENCOUNTER_CHANCE_FISHING_MONS_*_SLOT_n` defines - but the code that uses them,
`ChooseWildMonIndex_Fishing` in `src/wild_encounter.c`, is hand-written against
fixed slot numbers. Changing the split in Porymap therefore breaks the build
with an undeclared `ENCOUNTER_CHANCE_*`, which is the lucky outcome.

The quieter trap is the rates. `rand` is drawn against the **largest** of the
three rod totals, so a rod summing to less than that has a dead band at the top
where no slot matches and `wildMonIndex` keeps its initial `0` - a super rod
handing out an old-rod Pokemon. Vanilla is safe only because all three sum to
100. **Keep every rod's rates summing to the same number.**

**`include/constants/opponents.h` is NOT generated.** `trainerproc` emits
`src/data/trainers.h` from `trainers.party`, but the `TRAINER_*` constants and
`TRAINERS_COUNT` are hand-maintained, so a new trainer needs an entry in both
files or the build fails with "undeclared here (not in a function)". **Append**
new trainers rather than inserting, so no existing id shifts, and leave
`MAX_TRAINERS_COUNT` alone unless the count actually exceeds it - it is the
base for `TRAINER_PARTNER`, so raising it moves every partner id.

**Cut trees respawn unless given a permanent flag.** Vanilla points them at
`FLAG_TEMP_11`, which is cleared on every map change. `removeobject` sets
whichever flag the object names, so naming a real flag makes the cut stick.

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
| HM gating | `src/field_move.c` — `BADGE_UNLOCK` keys off badge *number*; `FLAG_UNLOCK` (ours) names a flag instead, via `sFieldMoveUnlockFlags` |
| Trainer parties | `src/data/trainers.party` (Showdown syntax, 855 trainers) |
| Debug test parties | `src/data/debug_trainers.party` — player + AI side for *Set Party* / *Start Debug Battle* |
| Hack debug menu | `data/scripts/debug_hack.inc` + tables in `src/debug.c` |
| Level-cap announcement | `data/scripts/level_cap.inc` (`Common_EventScript_LevelCapIncreased`) |
| Calc exporter | `tools/calc_export.py` — see §4b |
| Held-item restore | `TryRestoreHeldItems` in `src/battle_util.c` |
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
rebuilt · Route 102/103/104 NPC and terrain work · Norman's advice points east
to Wattson and on to Lucy · Scott leaves Petalburg eastward instead of walking
through the Aqua blockade · **Birch hands over the PokéNav on Route 110** ·
`Hack…` debug menu · 99 Poké Balls from the rival · held consumables are never
spent · **Wally's uncle blocks the Mauville Gym** and the Wally battle moved to
Wanda's House · **Gate D (Verdanturf Aqua grunt)** · level cap 22 for beating
Wally, announced on screen after every cap-raising fight · obedience restricted
to traded Pokémon · Terastal suppressed · `Smart Trainer` no longer mid-battle
pivots · **damage calculator with save import** (§4b) · HMs are forgettable
(`P_CAN_FORGET_HIDDEN_MOVE`) · debug box fill with every wild species · **Lucy's Fallarbor gym** (three relocated route trainers, VENOM BADGE, TM Sludge Bomb) · HM field moves need only the badge and the HM, not a party Pokemon that knows it (`OW_FIELD_MOVE_NEEDS_PARTY_MOVE`) · **Route 114**: the Cut gate and its HM giver, and Aqua Admins Matt and Shelly double-battling in front of Meteor Falls.

**Open:**
- **Gate D's opening condition** — the blockade is built, but nothing sets
  `STORY_GATE_D_OPEN`, so the grunt never leaves.
- **Gate C (Slateport)** — condition undefined.
- **Scott's Mauville cameo is orphaned.** It lived in
  `MauvilleCity_EventScript_DefeatedWally`, which no longer runs; it also owned
  `VAR_SCOTT_STATE`. Wanda's introduction and Wally's first Match Call were
  re-homed into the Wanda's House battle, but Scott still needs somewhere to go.
- Scott's Petalburg dialogue (his movement is done).
- **Badges past eight.** Eleven gyms are planned against eight contiguous
  `FLAG_BADGE0X_GET` flags, so Lucy's VENOM BADGE is cosmetic and does not show
  on the trainer card. Real support means more flags, card art and layout.
- **Cut now arrives at gym 2**; cuttable trees in the east are unaudited.
- **Matt and Shelly's parties are placeholders**, as is their dialogue.
- Birch's farewell line on Route 110 is still vanilla, and still asks the
  player to look out for the rival.
- Mr. Stone's Rustboro scene still hands out a second PokéNav.
- The remaining ~850 trainers *(user-owned)*.
- New rivals, new Megas, new gyms.
- `FLAG_CAP_TBD_AFTER_WATTSON` is a placeholder — the cap holds at 24 after
  Wattson until the next milestone is designed.

**Known test state.** `make check` reports **5395 passed / 14 failed**. All 14
are consequences of this hack's config, not regressions: hard level caps break
`test/battle/exp.c`, the added story var shifts `SaveBlock1` by 4 bytes
(`test/save.c`), disabled EVs break the Embargo EV test, and several AI and
multi-hit tests are randomness-sensitive. Treat that set as the baseline and
diff against it rather than reading a red number as breakage.
