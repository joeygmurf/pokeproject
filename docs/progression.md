# Progression Plan — Reordered Hoenn

Working spec for this hack's custom story order. **Covers the opening through
Wattson (first gym) only** — later stages get appended as they're designed.

The point of this document is to catch softlocks and sequence breaks on paper,
before any script is written. Every gate must have: something that blocks it, a
single condition that opens it, and a reason the player cannot route around it.

---

## 1. Design intent

Vanilla Emerald runs Roxanne → Brawly → Wattson → Flannery → Norman → Winona →
Tate&Liza → Juan, with the player pushed west from Petalburg into Route 104 and
Rustboro.

This hack sends the player **east instead**, making **Wattson the first gym**.
Route 104 is sealed, and Route 103's water crossing becomes a sand path that
opens after the Petalburg intro.

---

## 2. Opening sequence

| # | Step | Notes |
|---|---|---|
| 1 | Littleroot → Route 101 → Oldale | unchanged |
| 2 | Route 102 → Petalburg City | unchanged |
| 3 | Petalburg: Norman intro + help Wally catch Ralts | unchanged. **No gym battle, no badge.** |
| 4 | Player tries west to Route 104 | **BLOCKED** — Team Aqua (Gate A) |
| 5 | Scott appears, mentions the blockade, points at Route 103 | reuses the vanilla Scott trigger |
| 6 | Back east to Route 103 | sand path across the former water |
| 7 | Route 103 crossing | **BLOCKED until step 3 is done** (Gate B) |
| 8 | Route 103 → Route 110 | south to Slateport is **BLOCKED** (Gate C) |
| 9 | Route 110: rival battle | unchanged from vanilla |
| 10 | Route 110 → Mauville | |
| 11 | **Wattson — first gym.** Dynamo Badge | Wally's pre-gym scene **removed** (see §6) |
| 12 | Rock Smash becomes usable; Route 111 north opens | works unmodified — see §5 |
| 13 | Rusturf Tunnel (Verdanturf → Route 116) | **BLOCKED** (Gate D) |

---

## 3. Gates

### Gate A — Route 104, west of Petalburg — **BUILT**
- **Blocks:** Petalburg → Route 104, and therefore Petalburg Woods, Rustboro,
  Dewford, Mr. Briney, and the whole western half of the early game.
- **Opens:** `VAR_STORY_PROGRESS >= STORY_ROXANNE_DEFEATED`, set by Rustboro
  Gym alongside the Stone Badge.
- **Enforced by:** two Team Aqua grunts at **(1,12)** and **(1,13)**. Petalburg's
  west edge has exactly two walkable tiles, (0,12) and (0,13), so the pair
  closes it completely — verified by flood fill. They face left, turn to the
  player when spoken to, refuse passage, and turn back. Hidden by
  `FLAG_HIDE_PETALBURG_AQUA_BLOCKADE`, set from Petalburg's `ON_TRANSITION`.
- **Why it can't be routed around:** Route 104 is reachable only from Petalburg
  (right), Rustboro (up) and Route 105 (down, requires Surf). Rustboro is itself
  gated by Gate D. Surf is locked behind Norman's badge.

### Gate B — Route 103 crossing — **BUILT**
- **Blocks:** Route 103 → Route 110, i.e. the entire new critical path.
- **Opens:** `VAR_STORY_PROGRESS >= STORY_WALLY_TUTORIAL_DONE`, set in Petalburg
  the instant Wally catches his Ralts. (`Route103_EventScript_MigrateStoryProgress`
  brings pre-existing saves up to date; removable once none matter.)
- **Enforced by:** the boy at **(24,11)**, verified to be a single tile that
  seals the sand crossing on its own. He steps up to (24,10) when it opens.
  Position is driven from `Route103_OnTransition` with `setobjectxyperm`.
- **Dialogue:** no Pokédex → *"I wouldn't go further than this without a
  POKéDEX!"*; intro unfinished → points back at the Petalburg Gym; open →
  *"Lots of strong TRAINERS are ahead."*
- **Why it can't be routed around:** Route 110 connects only to Route 103
  (left), Mauville (up) and Slateport (down). Mauville is behind this gate;
  Slateport is behind Gate C.

> **Trap, learned the hard way.** `VAR_PETALBURG_CITY_STATE` spans two
> unrelated story beats. 2 and 3 are the early intro (3 is set the instant
> Wally catches his Ralts); **4 and 5 are the POST-Norman sequence**, where
> Wally's dad walks the player home and hands over HM Surf. Gating on 5 meant
> the crossing only opened after Norman was beaten and Surf obtained - the
> exact progression this design exists to prevent.
>
> This is the argument for a dedicated `VAR_STORY_PROGRESS`: vanilla state
> vars get reused across beats, so a numeric comparison can silently span a
> gap you did not intend. Adopt it before Gate A.

### Gate C — Slateport
- **Blocks:** Route 110 → Slateport.
- **Opens:** TBD.
- **Enforced by:** the existing Team Aqua blockade — **needs verification** that
  vanilla's blockade sits where we need it and is driven by a flag we can hold.

### Gate D — Rusturf Tunnel
- **Blocks:** Verdanturf → Route 116 → Rustboro.
- **Opens:** TBD — must stay shut until the western half is meant to open.
- **Enforced by:** NPC inside the tunnel.
- **Why this one matters most:** Wattson is now the *first* gym, so **Rock Smash
  arrives far earlier than vanilla**. The tunnel's vanilla rock barrier is no
  longer a gate at all — without an NPC the player smashes straight through to
  Rustboro and skips the intended order entirely.

---

## 4. Level caps

Vanilla badges are no longer earned in numerical order, which **breaks the
existing cap table**: `GetCurrentLevelCap` (`src/caps.c:8`) returns the cap for
the first *unset* flag, so with Wattson first (`FLAG_BADGE03_GET`) and
`FLAG_BADGE01_GET` still unset, the cap would stay at 15 for the whole game.

`sLevelCapFlagMap` accepts **any** flags, so the fix is a ladder of custom
progression flags, letting rival fights and story beats raise the cap too:

Each row is `{flag, cap while that milestone is still pending}` — the same
semantics vanilla used, where `{FLAG_BADGE01_GET, 15}` meant "cap 15 until
Roxanne falls".

| Cap | Applies during | Flag | Set by |
|---|---|---|---|
| 15 | opening → Route 110 rival | `FLAG_CAP_RIVAL_ROUTE110` | `Route110_EventScript_RivalExit` |
| 19 | rival beaten → Wattson | `FLAG_CAP_WATTSON` | `MauvilleCity_Gym` badge block |
| 24 | after Wattson | `FLAG_CAP_TBD_AFTER_WATTSON` | **nothing yet — placeholder** |
| 58 | post-Champion | `FLAG_IS_CHAMPION` | vanilla |

The cap therefore holds at 24 after Wattson until the next milestone is
designed. Fine while only the opening is reordered; revisit before extending
play past Mauville.

Constraint: flags must be set in list order, which holds as long as the spine is
linear. If a stretch ever becomes non-linear, switch to `LEVEL_CAP_VARIABLE`
(`B_LEVEL_CAP_TYPE` in `include/config/caps.h`) and have each milestone
`setvar` the cap directly.

**Dormant landmine:** `sEvCapFlagMap` (`src/caps.c:92`) still assumes badges are
earned in numerical order and has the same flaw. It is unreachable today because
`B_EV_CAP_TYPE` is `EV_CAP_NO_GAIN`. If EV caps are ever re-enabled, remap it
the same way.

---

## 5. HM availability

HM → badge mapping lives in one table in `src/field_move.c`:

| HM | Badge | Gym | When, in this hack |
|---|---|---|---|
| Cut | 01 | Roxanne | late — keeps Petalburg Woods / Route 104 trees shut |
| Flash | 02 | Brawly | late |
| **Rock Smash** | **03** | **Wattson** | **first** — intended |
| Strength | 04 | Flannery | |
| Surf | 05 | Norman | **must stay late** — Surf trivialises Gates A and B |

Rock Smash already sits on Wattson's badge, so it needs **no change**. Cut
arriving late is convenient: it reinforces Gate A rather than fighting it.

**Surf is the single most dangerous item in this design.** It bypasses Gate B
entirely (Route 103's water) and reaches Route 104 from Route 105. Norman must
not be beatable early.

---

## 6. Other edits

- **Route 103 terrain — DONE.** The water crossing is now a sand beach at
  y10–12, x22–48. Shoreline follows the tileset's own convention (see
  `docs/PROJECT.md`, "Hoenn shoreline tiling").
- **Old Rod fisherman — DONE.** Moved from Dewford to Petalburg (10,22);
  Dewford is behind Gate A, so the rod would have been unobtainable.
- **Early-game encounters — DONE.** Grass patches added to Littleroot (fenced,
  gated on owning a Pokémon) and Oldale, both with their own wild data, because
  only five species were reachable before the Route 103 crossing.
- **Starter met location — DONE.** Recorded as `METLOC_FATEFUL_ENCOUNTER`
  instead of Route 101, so a Nuzlocke still gets a Route 101 encounter.
- **Wally's Mauville pre-gym scene** — TODO: remove; the player just saw him in
  Petalburg. Relocate the encounter later.
- **Scott** — TODO: reuse the vanilla trigger, new dialogue referencing the
  blockade and pointing at Route 103.

---

## 7. Open problems

1. **Devon Goods questline — deferred to mid-story (decided 2026-10-09).**
   In vanilla it is the spine of the *early* game: an Aqua grunt steals the
   goods on Route 116, you chase him through Rusturf Tunnel, deliver to Devon in
   Rustboro, then carry the parcel to Slateport. Rustboro now comes late, so the
   chain moves with it and becomes mid-game content rather than the opening.
   Nothing to solve before Gates A/C/D — just do not let the opening depend on
   any of its flags.
2. **Gate C and Gate D opening conditions** are undefined. Both can now be
   written against `VAR_STORY_PROGRESS`; `STORY_GATE_D_OPEN` is reserved.
3. **Gate A** opens at `STORY_ROXANNE_DEFEATED`, which is reserved but not yet
   set anywhere — Rustboro Gym needs to set it when that stage is built.
4. **NPC dialogue across the region** will reference the vanilla order. Long tail,
   not hard, but wide.
5. **Match Call / TV / rival systems** assume vanilla progression.

---

## 8. Working rules

- Add **one gate at a time**, verify it, commit. Never leave the game
  half-reordered.
- Prefer a **new dedicated var** for custom story state over overloading
  vanilla `VAR_*_STATE` vars, which are load-bearing for event chains.
- After each gate, verify with a reachability check (see `tools/mapview.py` and
  the flood-fill approach used for Route 102) that the gate cannot be walked,
  surfed, or smashed around.
- Expect mid-development saves to go stale; use the debug menu (R + START) to
  set flags/vars and jump to the section under test.
