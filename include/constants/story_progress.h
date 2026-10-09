#ifndef GUARD_CONSTANTS_STORY_PROGRESS_H
#define GUARD_CONSTANTS_STORY_PROGRESS_H

// The story spine for this hack's reordered Hoenn. See docs/progression.md.
//
// VAR_STORY_PROGRESS is the single authority for where the player is in the
// custom order. Every new gate compares against it and nothing else.
//
// Why not reuse vanilla's VAR_*_STATE vars: they get recycled across unrelated
// story beats. VAR_PETALBURG_CITY_STATE is 2-3 during the early Wally intro but
// 4-5 during the POST-Norman sequence that hands over HM Surf, so a ">= 5"
// gate silently required Surf. A var we own cannot drift onto someone else's
// meaning.
//
// Values are spaced by 10 so milestones can be inserted later without
// renumbering, and gates should always use >= so an inserted step does not
// reopen a gate that was already closed.
//
// Monotonic: these are one-time story events, so the var only ever increases.
// If a beat could ever fire twice, guard it with a flag as well.

#define STORY_START                     0   // new game
#define STORY_WALLY_TUTORIAL_DONE      10   // Wally catches his Ralts; Gate B (Route 103 crossing) opens
#define STORY_RIVAL_ROUTE110           20   // rival beaten on Route 110
#define STORY_WATTSON_DEFEATED         30   // first gym of this hack; Rock Smash becomes usable

// Reserved for milestones that are designed but not built yet, so gates can be
// written against them now:
#define STORY_ROXANNE_DEFEATED         40   // Gate A (Route 104 Aqua blockade) opens
#define STORY_GATE_D_OPEN              50   // Rusturf Tunnel opens to Route 116 / Rustboro

#endif // GUARD_CONSTANTS_STORY_PROGRESS_H
