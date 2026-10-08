@ Field menu opened with the L button in the overworld.
@ Triggered from ProcessPlayerFieldInput in src/field_control_avatar.c.
@ The menu reopens after an action so the REPEL colour change is visible;
@ EXIT or B closes it. lockall happens once, in _Open.

FieldMenu_EventScript_Open::
	lockall
	goto FieldMenu_EventScript_Show
	end

FieldMenu_EventScript_Show::
	goto_if_set FLAG_INFINITE_REPEL, FieldMenu_EventScript_ShowRepelOn
	multichoice 0, 0, MULTI_FIELD_MENU_REPEL_OFF, FALSE
	goto FieldMenu_EventScript_Handle
	end

FieldMenu_EventScript_ShowRepelOn::
	multichoice 0, 0, MULTI_FIELD_MENU_REPEL_ON, FALSE
	goto FieldMenu_EventScript_Handle
	end

FieldMenu_EventScript_Handle::
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
	closemessage
	goto FieldMenu_EventScript_Show
	end

FieldMenu_EventScript_ToggleRepel::
	goto_if_set FLAG_INFINITE_REPEL, FieldMenu_EventScript_RepelOff
	setflag FLAG_INFINITE_REPEL
	msgbox FieldMenu_Text_RepelOn, MSGBOX_DEFAULT
	closemessage
	goto FieldMenu_EventScript_Show
	end

FieldMenu_EventScript_RepelOff::
	clearflag FLAG_INFINITE_REPEL
	msgbox FieldMenu_Text_RepelOff, MSGBOX_DEFAULT
	closemessage
	goto FieldMenu_EventScript_Show
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
