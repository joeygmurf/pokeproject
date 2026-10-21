@ ============================================================================
@ Level cap announcement.
@
@ Call this at the END of any event that raises the cap, after the milestone
@ flag is set and after the NPC has finished talking. The number is read back
@ from GetCurrentLevelCap rather than written out per site, so it cannot drift
@ out of step with sLevelCapFlagMap in src/caps.c.
@
@ Callers must already hold a lock. Use `call`, not `goto`.
@ ============================================================================

	.align 2

Common_EventScript_LevelCapIncreased::
	callnative BufferCurrentLevelCap
	playfanfare MUS_OBTAIN_TMHM
	message Common_Text_LevelCapIncreased
	waitmessage
	waitfanfare
	closemessage
	return

Common_Text_LevelCapIncreased:
	.string "Level Cap Increased to {STR_VAR_1}!$"
