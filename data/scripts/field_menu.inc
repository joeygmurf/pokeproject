@ Field menu opened with the L button in the overworld.
@ Triggered from ProcessPlayerFieldInput in src/field_control_avatar.c.

FieldMenu_EventScript_Open::
	lockall
	multichoice 0, 0, MULTI_FIELD_MENU, FALSE
	switch VAR_RESULT
	case 0, FieldMenu_EventScript_PokeVial
	case 1, FieldMenu_EventScript_ToggleRepel
	case 2, FieldMenu_EventScript_Exit
	case MULTI_B_PRESSED, FieldMenu_EventScript_Exit
	goto FieldMenu_EventScript_Exit
	end

FieldMenu_EventScript_PokeVial::
	special HealPlayerParty
	playfanfare MUS_HEAL
	waitfanfare
	msgbox FieldMenu_Text_PartyHealed, MSGBOX_DEFAULT
	goto FieldMenu_EventScript_Exit
	end

FieldMenu_EventScript_ToggleRepel::
	goto_if_set FLAG_INFINITE_REPEL, FieldMenu_EventScript_RepelOff
	setflag FLAG_INFINITE_REPEL
	msgbox FieldMenu_Text_RepelOn, MSGBOX_DEFAULT
	goto FieldMenu_EventScript_Exit
	end

FieldMenu_EventScript_RepelOff::
	clearflag FLAG_INFINITE_REPEL
	msgbox FieldMenu_Text_RepelOff, MSGBOX_DEFAULT
	goto FieldMenu_EventScript_Exit
	end

FieldMenu_EventScript_Exit::
	closemessage
	releaseall
	end

FieldMenu_Text_PartyHealed:
	.string "Your POKéMON were restored to\n"
	.string "full health!$"

FieldMenu_Text_RepelOn:
	.string "Wild POKéMON will no longer\n"
	.string "appear.$"

FieldMenu_Text_RepelOff:
	.string "Wild POKéMON will appear\n"
	.string "normally again.$"
