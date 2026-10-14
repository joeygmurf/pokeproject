@ ============================================================================
@ Debug menu: this hack's own entries. Reached via R + START -> "Hack...".
@
@ Two groups:
@   Story jump... - move VAR_STORY_PROGRESS and everything that rides on it to
@                   a chosen milestone, so a gate can be retested without
@                   replaying up to it. See include/constants/story_progress.h.
@   Warp...       - land on the tiles the custom events actually fire from.
@
@ The story jumps are CUMULATIVE: each one calls the beats before it, so
@ picking "Wattson beaten" also applies Wally and the Route 110 rival. They do
@ not hand out Pokemon, badges you have not earned, or bag items - use the
@ stock "Cheat start" and "Give X..." menus for that.
@ ============================================================================

	.align 2

@ ---------------------------------------------------------------------------
@ Shared pieces
@ ---------------------------------------------------------------------------

Debug_Hack_ClearCapFlags::
	clearflag FLAG_CAP_RIVAL_ROUTE110
	clearflag FLAG_CAP_WATTSON
	clearflag FLAG_CAP_TBD_AFTER_WATTSON
	return

Debug_Hack_Done::
	msgbox Debug_Hack_Text_Done, MSGBOX_SIGN
	releaseall
	end

@ ---------------------------------------------------------------------------
@ Story jumps
@ ---------------------------------------------------------------------------

@ Back to a fresh spine. Badges and party are left alone - this only rewinds
@ the custom progression, so Gate A and Gate B close again.
Debug_Hack_Story_Start::
	setvar VAR_STORY_PROGRESS, STORY_START
	call Debug_Hack_ClearCapFlags
	setvar VAR_REGISTER_BIRCH_STATE, 0
	goto Debug_Hack_Done

@ Wally has caught his Ralts. Gate B (Route 103 crossing) opens and the
@ Route 110 Birch scene is armed, so this is the one to use when testing
@ either of those.
Debug_Hack_Story_WallyDone::
	call Debug_Hack_Beat_WallyDone
	goto Debug_Hack_Done

Debug_Hack_Beat_WallyDone::
	call Debug_Hack_ClearCapFlags
	setvar VAR_STORY_PROGRESS, STORY_WALLY_TUTORIAL_DONE
	setvar VAR_PETALBURG_CITY_STATE, 3
	setvar VAR_PETALBURG_GYM_STATE, 1
	setvar VAR_REGISTER_BIRCH_STATE, 1
	setflag FLAG_SYS_POKEDEX_GET
	return

@ Route 110 rival beaten. Level cap 19. Birch is marked as already met, so
@ his scene will not re-fire.
Debug_Hack_Story_RivalRoute110::
	call Debug_Hack_Beat_WallyDone
	call Debug_Hack_Beat_RivalRoute110
	goto Debug_Hack_Done

Debug_Hack_Beat_RivalRoute110::
	setvar VAR_STORY_PROGRESS, STORY_RIVAL_ROUTE110
	setflag FLAG_CAP_RIVAL_ROUTE110
	setvar VAR_ROUTE110_STATE, 1
	setvar VAR_REGISTER_BIRCH_STATE, 2
	setflag FLAG_SYS_POKENAV_GET
	setflag FLAG_RECEIVED_POKENAV
	setflag FLAG_ADDED_MATCH_CALL_TO_POKENAV
	setflag FLAG_ENABLE_PROF_BIRCH_MATCH_CALL
	return

@ Wattson beaten - first gym of this hack. Dynamo Badge, Rock Smash usable,
@ level cap 24. Mirrors MauvilleCity_Gym_EventScript_WattsonDefeated.
Debug_Hack_Story_WattsonDefeated::
	call Debug_Hack_Beat_WallyDone
	call Debug_Hack_Beat_RivalRoute110
	call Debug_Hack_Beat_WattsonDefeated
	goto Debug_Hack_Done

Debug_Hack_Beat_WattsonDefeated::
	setvar VAR_STORY_PROGRESS, STORY_WATTSON_DEFEATED
	setflag FLAG_BADGE03_GET
	setflag FLAG_DEFEATED_MAUVILLE_GYM
	setflag FLAG_CAP_WATTSON
	setvar VAR_SLATEPORT_OUTSIDE_MUSEUM_STATE, 3
	clearflag FLAG_HIDE_VERDANTURF_TOWN_SCOTT
	return

@ Reserved milestone: Gate A (the Petalburg Aqua blockade) opens here. Nothing
@ in the game sets STORY_ROXANNE_DEFEATED yet, so this is the only way to see
@ the west half open.
Debug_Hack_Story_RoxanneDefeated::
	call Debug_Hack_Beat_WallyDone
	call Debug_Hack_Beat_RivalRoute110
	call Debug_Hack_Beat_WattsonDefeated
	setvar VAR_STORY_PROGRESS, STORY_ROXANNE_DEFEATED
	setflag FLAG_BADGE01_GET
	goto Debug_Hack_Done

@ ---------------------------------------------------------------------------
@ Warps
@
@ Each lands a short walk from the event it is named for, facing into it, so
@ the trigger still has to fire normally. Coordinates verified walkable.
@ To add one: copy a line below, add a matching entry in src/debug.c.
@ ---------------------------------------------------------------------------

Debug_Hack_Warp_Littleroot::            @ grass gate girl
	warp MAP_LITTLEROOT_TOWN, 14, 12
	waitstate
	releaseall
	end

Debug_Hack_Warp_Route102::              @ tree block, Rick and Allen
	warp MAP_ROUTE102, 24, 13
	waitstate
	releaseall
	end

Debug_Hack_Warp_Route103::              @ Gate B, west side of the sand crossing
	warp MAP_ROUTE103, 20, 11
	waitstate
	releaseall
	end

Debug_Hack_Warp_Petalburg::             @ east of the Scott trigger; walk west
	warp MAP_PETALBURG_CITY, 10, 12
	waitstate
	releaseall
	end

Debug_Hack_Warp_Route110Birch::         @ west of the Birch trigger; walk east
	warp MAP_ROUTE110, 6, 70
	waitstate
	releaseall
	end

Debug_Hack_Warp_Route110Rival::         @ below the rival trigger row; walk up
	warp MAP_ROUTE110, 35, 58
	waitstate
	releaseall
	end

Debug_Hack_Warp_MauvilleGym::           @ two tiles below the gym door
	warp MAP_MAUVILLE_CITY, 8, 7
	waitstate
	releaseall
	end

@ ---------------------------------------------------------------------------

Debug_Hack_Text_Done:
	.string "Story progress set.$"
