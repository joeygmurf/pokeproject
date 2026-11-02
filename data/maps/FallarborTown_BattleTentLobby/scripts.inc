FallarborTown_BattleTentLobby_MapScripts::
	map_script MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE, FallarborTown_BattleTentLobby_OnWarp
	.byte 0

FallarborTown_BattleTentLobby_OnWarp:
	map_script_2 VAR_TEMP_1, 0, FallarborTown_BattleTentLobby_EventScript_TurnPlayerNorth
	.2byte 0

FallarborTown_BattleTentLobby_EventScript_TurnPlayerNorth::
	setvar VAR_TEMP_1, 1
	turnobject LOCALID_PLAYER, DIR_NORTH
	end

FallarborTown_BattleTentLobby_EventScript_GetChallengeStatus::
	frontier_getstatus
	end

FallarborTown_BattleTentLobby_EventScript_QuitWithoutSaving::
	lockall
	msgbox FallarborTown_BattleTentLobby_Text_DidntSaveBeforeQuitting, MSGBOX_DEFAULT
	closemessage
	frontier_set FRONTIER_DATA_CHALLENGE_STATUS, 0
	setvar VAR_TEMP_CHALLENGE_STATUS, 255
	frontier_set FRONTIER_DATA_LVL_MODE, FRONTIER_LVL_50
	releaseall
	end

FallarborTown_BattleTentLobby_EventScript_WonChallenge::
	lockall
	msgbox FallarborTown_BattleTentLobby_Text_BeatThreeTrainers, MSGBOX_DEFAULT
	message FallarborTown_BattleTentLobby_Text_WaitWhileSaveGame
	waitmessage
	fallarbortent_setrandomprize
	frontier_set FRONTIER_DATA_LVL_MODE, FRONTIER_LVL_50
	fallarbortent_save 0
	playse SE_SAVE
	waitse

FallarborTown_BattleTentLobby_EventScript_GivePrize::
	msgbox FallarborTown_BattleTentLobby_Text_PresentYouWithPrize, MSGBOX_DEFAULT
	fallarbortent_giveprize
	switch VAR_RESULT
	case FALSE, FallarborTown_BattleTentLobby_EventScript_NoRoomForPrize
	frontier_set FRONTIER_DATA_CHALLENGE_STATUS, 0
	message FallarborTown_BattleTentLobby_Text_ReceivedPrize
	waitmessage
	playfanfare MUS_OBTAIN_ITEM
	waitfanfare
	msgbox FallarborTown_BattleTentLobby_Text_AwaitAnotherChallenge2, MSGBOX_DEFAULT
	closemessage
	setvar VAR_TEMP_CHALLENGE_STATUS, 255
	releaseall
	end

FallarborTown_BattleTentLobby_EventScript_NoRoomForPrize::
	msgbox FallarborTown_BattleTentLobby_Text_BagFullReturnForPrize, MSGBOX_DEFAULT
	waitmessage
	closemessage
	setvar VAR_TEMP_CHALLENGE_STATUS, 255
	releaseall
	end

FallarborTown_BattleTentLobby_EventScript_PrizeWaiting::
	lockall
	msgbox FallarborTown_BattleTentLobby_Text_BeatThreeTrainers, MSGBOX_DEFAULT
	goto FallarborTown_BattleTentLobby_EventScript_GivePrize
	end

FallarborTown_BattleTentLobby_EventScript_LostChallenge::
	lockall
	message FallarborTown_BattleTentLobby_Text_ThankYouWaitWhileSaving
	waitmessage
	frontier_set FRONTIER_DATA_LVL_MODE, FRONTIER_LVL_50
	fallarbortent_save 0
	playse SE_SAVE
	waitse
	msgbox FallarborTown_BattleTentLobby_Text_AwaitAnotherChallenge2, MSGBOX_DEFAULT
	closemessage
	setvar VAR_TEMP_CHALLENGE_STATUS, 255
	releaseall
	end

FallarborTown_BattleTentLobby_EventScript_ResumeChallenge::
	lockall
	message FallarborTown_BattleTentLobby_Text_LookingForwardToArrival
	waitmessage
	fallarbortent_save CHALLENGE_STATUS_SAVING
	playse SE_SAVE
	waitse
	frontier_set FRONTIER_DATA_PAUSED, FALSE
	setvar VAR_TEMP_CHALLENGE_STATUS, 255
	goto FallarborTown_BattleTentLobby_EventScript_EnterChallenge

FallarborTown_BattleTentLobby_EventScript_Attendant::
	lock
	faceplayer
	fallarbortent_getprize
	goto_if_ne VAR_RESULT, ITEM_NONE, FallarborTown_BattleTentLobby_EventScript_PrizeWaiting
	special SavePlayerParty
	msgbox FallarborTown_BattleTentLobby_Text_WelcomeToBattleTent, MSGBOX_DEFAULT
FallarborTown_BattleTentLobby_EventScript_AskEnterChallenge::
	message FallarborTown_BattleTentLobby_Text_TakeChallenge
	waitmessage
	multichoice 17, 6, MULTI_CHALLENGEINFO, FALSE
	switch VAR_RESULT
	case 0, FallarborTown_BattleTentLobby_EventScript_TryEnterChallenge
	case 1, FallarborTown_BattleTentLobby_EventScript_ExplainChallenge
	case 2, FallarborTown_BattleTentLobby_EventScript_CancelChallenge
	case MULTI_B_PRESSED, FallarborTown_BattleTentLobby_EventScript_CancelChallenge

FallarborTown_BattleTentLobby_EventScript_TryEnterChallenge::
	setvar VAR_FRONTIER_FACILITY, FRONTIER_FACILITY_ARENA
	setvar VAR_FRONTIER_BATTLE_MODE, FRONTIER_MODE_SINGLES
	setvar VAR_RESULT, 2
	frontier_checkineligible
	goto_if_eq VAR_0x8004, TRUE, FallarborTown_BattleTentLobby_EventScript_NotEnoughValidMons
	frontier_set FRONTIER_DATA_LVL_MODE, FRONTIER_LVL_TENT
	msgbox FallarborTown_BattleTentLobby_Text_SelectThreeMons, MSGBOX_DEFAULT
	fadescreen FADE_TO_BLACK
	setvar VAR_0x8004, 2
	setvar VAR_0x8005, FRONTIER_PARTY_SIZE
	special ChoosePartyForBattleFrontier
	goto_if_eq VAR_RESULT, 0, FallarborTown_BattleTentLobby_EventScript_LoadPartyCancelChallenge
	msgbox FallarborTown_BattleTentLobby_Text_SaveBeforeChallenge, MSGBOX_YESNO
	switch VAR_RESULT
	case NO, FallarborTown_BattleTentLobby_EventScript_LoadPartyCancelChallenge
	case YES, FallarborTown_BattleTentLobby_EventScript_SaveBeforeChallenge
	case MULTI_B_PRESSED, FallarborTown_BattleTentLobby_EventScript_LoadPartyCancelChallenge

FallarborTown_BattleTentLobby_EventScript_SaveBeforeChallenge::
	setvar VAR_TEMP_CHALLENGE_STATUS, 0
	frontier_set FRONTIER_DATA_SELECTED_MON_ORDER
	fallarbortent_init
	frontier_set FRONTIER_DATA_CHALLENGE_STATUS, CHALLENGE_STATUS_SAVING
	frontier_set FRONTIER_DATA_PAUSED, FALSE
	special LoadPlayerParty
	closemessage
	delay 2
	call Common_EventScript_SaveGame
	setvar VAR_TEMP_CHALLENGE_STATUS, 255
	goto_if_eq VAR_RESULT, 0, FallarborTown_BattleTentLobby_EventScript_CancelChallengeSaveFailed
FallarborTown_BattleTentLobby_EventScript_EnterChallenge::
	special SavePlayerParty
	frontier_setpartyorder FRONTIER_PARTY_SIZE
	msgbox FallarborTown_BattleTentLobby_Text_GuideYouToBattleTent, MSGBOX_DEFAULT
	closemessage
	call FallarborTown_BattleTentLobby_EventScript_WalkToDoor
	warp MAP_FALLARBOR_TOWN_BATTLE_TENT_CORRIDOR, 2, 7
	setvar VAR_TEMP_CHALLENGE_STATUS, 0
	waitstate
	end

FallarborTown_BattleTentLobby_EventScript_ExplainChallenge::
	msgbox FallarborTown_BattleTentLobby_Text_ExplainFallarborTent, MSGBOX_DEFAULT
	goto FallarborTown_BattleTentLobby_EventScript_AskEnterChallenge

FallarborTown_BattleTentLobby_EventScript_NotEnoughValidMons::
	switch VAR_RESULT
	case FRONTIER_LVL_50, FallarborTown_BattleTentLobby_EventScript_NotEnoughValidMonsLv50
	case FRONTIER_LVL_OPEN, FallarborTown_BattleTentLobby_EventScript_NotEnoughValidMonsLvOpen
FallarborTown_BattleTentLobby_EventScript_NotEnoughValidMonsLv50::
	msgbox FallarborTown_BattleTentLobby_Text_NotEnoughValidMonsLv50, MSGBOX_DEFAULT
	goto FallarborTown_BattleTentLobby_EventScript_EndCancelChallenge

FallarborTown_BattleTentLobby_EventScript_NotEnoughValidMonsLvOpen::
	msgbox FallarborTown_BattleTentLobby_Text_NotEnoughValidMonsLvOpen, MSGBOX_DEFAULT
	goto FallarborTown_BattleTentLobby_EventScript_EndCancelChallenge

FallarborTown_BattleTentLobby_EventScript_CancelChallengeSaveFailed::
	frontier_set FRONTIER_DATA_CHALLENGE_STATUS, 0
	goto FallarborTown_BattleTentLobby_EventScript_CancelChallenge

FallarborTown_BattleTentLobby_EventScript_LoadPartyCancelChallenge::
	special LoadPlayerParty
FallarborTown_BattleTentLobby_EventScript_CancelChallenge::
	msgbox FallarborTown_BattleTentLobby_Text_AwaitAnotherChallenge, MSGBOX_DEFAULT
FallarborTown_BattleTentLobby_EventScript_EndCancelChallenge::
	release
	end

FallarborTown_BattleTentLobby_EventScript_WalkToDoor::
	applymovement LOCALID_FALLARBOR_GYM_LUCY, FallarborTown_BattleTentLobby_Movement_AttendantWalkToDoor
	applymovement LOCALID_PLAYER, FallarborTown_BattleTentLobby_Movement_PlayerWalkToDoor
	waitmovement 0
	opendoor 6, 1
	waitdooranim
	applymovement LOCALID_FALLARBOR_GYM_LUCY, FallarborTown_BattleTentLobby_Movement_AttendantEnterDoor
	applymovement LOCALID_PLAYER, FallarborTown_BattleTentLobby_Movement_PlayerEnterDoor
	waitmovement 0
	closedoor 6, 1
	waitdooranim
	return

FallarborTown_BattleTentLobby_Movement_AttendantWalkToDoor:
	walk_up
	walk_up
	walk_up
	step_end

FallarborTown_BattleTentLobby_Movement_AttendantEnterDoor:
	walk_up
	set_invisible
	step_end

FallarborTown_BattleTentLobby_Movement_PlayerWalkToDoor:
	walk_up
	walk_up
	walk_up
	step_end

FallarborTown_BattleTentLobby_Movement_PlayerEnterDoor:
	walk_up
	walk_up
	set_invisible
	step_end




@ Lucy's gym trainers. Moved here from Route 113 (Sophie, Coby) and Route 114
@ (Claude) rather than adding new trainer entries, so TRAINER_SOPHIE,
@ TRAINER_COBY and TRAINER_CLAUDE in trainers.party are reused unchanged.
@ Their text still lives under the old Route113_/Route114_ labels in
@ data/text/trainers.inc; rename when the gym dialogue is written.
FallarborTown_BattleTentLobby_EventScript_Coby::
	trainerbattle_single TRAINER_COBY, Route113_Text_CobyIntro, Route113_Text_CobyDefeat
	msgbox Route113_Text_CobyPostBattle, MSGBOX_AUTOCLOSE
	end

FallarborTown_BattleTentLobby_EventScript_Claude::
	trainerbattle_single TRAINER_CLAUDE, Route114_Text_ClaudeIntro, Route114_Text_ClaudeDefeat
	msgbox Route114_Text_ClaudePostBattle, MSGBOX_AUTOCLOSE
	end

FallarborTown_BattleTentLobby_EventScript_Sophie::
	trainerbattle_single TRAINER_SOPHIE, Route113_Text_SophieIntro, Route113_Text_SophieDefeat
	msgbox Route113_Text_SophiePostBattle, MSGBOX_AUTOCLOSE
	end

@ Gym Leader Lucy. Reuses TRAINER_LUCY, the Pike Queen's existing entry -
@ frontier_util.c still lists it as the Pike brain, which is harmless while the
@ Battle Frontier is unused, but would need splitting if it ever returns.
@ TODO: no badge is granted yet. Which FLAG_BADGE0X_GET she sets also decides
@ which HM she unlocks, because src/field_move.c maps HMs by badge number, not
@ by leader. She also needs a level-cap rung in src/caps.c once that is picked.
FallarborTown_BattleTentLobby_EventScript_Lucy::
	trainerbattle_single TRAINER_LUCY, FallarborTown_BattleTentLobby_Text_LucyIntro, FallarborTown_BattleTentLobby_Text_LucyDefeat, FallarborTown_BattleTentLobby_EventScript_LucyDefeated, NO_MUSIC
	goto_if_unset FLAG_RECEIVED_TM_SLUDGE_BOMB, FallarborTown_BattleTentLobby_EventScript_LucyOfferTmAgain
	msgbox FallarborTown_BattleTentLobby_Text_LucyPostBattle, MSGBOX_DEFAULT
	release
	end

FallarborTown_BattleTentLobby_EventScript_LucyDefeated::
	msgbox FallarborTown_BattleTentLobby_Text_LucyTakeThis, MSGBOX_DEFAULT
	setflag FLAG_DEFEATED_FALLARBOR_GYM
	call FallarborTown_BattleTentLobby_EventScript_GiveSludgeBomb
	release
	end

@ Reached only if the bag was full when the TM was first offered.
FallarborTown_BattleTentLobby_EventScript_LucyOfferTmAgain::
	msgbox FallarborTown_BattleTentLobby_Text_LucyTakeThis, MSGBOX_DEFAULT
	call FallarborTown_BattleTentLobby_EventScript_GiveSludgeBomb
	release
	end

FallarborTown_BattleTentLobby_EventScript_GiveSludgeBomb::
	giveitem ITEM_TM_SLUDGE_BOMB
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_BagIsFull
	msgbox FallarborTown_BattleTentLobby_Text_ExplainSludgeBomb, MSGBOX_DEFAULT
	setflag FLAG_RECEIVED_TM_SLUDGE_BOMB
	return

FallarborTown_BattleTentLobby_Text_LucyIntro:
	.string "I am LUCY…\p"
	.string "I used to be the PIKE QUEEN, but\n"
	.string "now I am the GYM LEADER here in\l"
	.string "FALLARBOR.\p"
	.string "I'm not one for idle chatter.\n"
	.string "Hurry. Come on…\p"
	.string "I hope you didn't use up all of\n"
	.string "your luck on the way here.$"

FallarborTown_BattleTentLobby_Text_LucyDefeat:
	.string "……Urk.$"

FallarborTown_BattleTentLobby_Text_LucyTakeThis:
	.string "You're strong. I'll acknowledge\n"
	.string "that.\p"
	.string "Take this.$"

FallarborTown_BattleTentLobby_Text_ExplainSludgeBomb:
	.string "That contains SLUDGE BOMB, a strong\n"
	.string "move that has a chance to poison\l"
	.string "your target.\p"
	.string "That's all. Disappear already…$"

FallarborTown_BattleTentLobby_Text_LucyPostBattle:
	.string "There is nothing else to be said\n"
	.string "here…$"

FallarborTown_BattleTentLobby_EventScript_Scott::
	lock
	faceplayer
	goto_if_set FLAG_MET_SCOTT_IN_FALLARBOR, FallarborTown_BattleTentLobby_EventScript_ScottAlreadySpokenTo
	msgbox FallarborTown_BattleTentLobby_Text_ScottLookingForSomeone, MSGBOX_DEFAULT
	addvar VAR_SCOTT_STATE, 1
	setflag FLAG_MET_SCOTT_IN_FALLARBOR
	release
	end

FallarborTown_BattleTentLobby_EventScript_ScottAlreadySpokenTo::
	msgbox FallarborTown_BattleTentLobby_Text_ScottMakeChallenge, MSGBOX_DEFAULT
	release
	end

FallarborTown_BattleTentLobby_EventScript_RulesBoard::
	lockall
	msgbox BattleFrontier_BattleArenaLobby_Text_RulesAreListed, MSGBOX_DEFAULT
	goto FallarborTown_BattleTentLobby_EventScript_ReadRulesBoard
	end

FallarborTown_BattleTentLobby_EventScript_ReadRulesBoard::
	message BattleFrontier_BattleArenaLobby_Text_ReadWhichHeading
	waitmessage
	multichoice 17, 0, MULTI_FALLARBOR_TENT_RULES, FALSE
	switch VAR_RESULT
	case 0, FallarborTown_BattleTentLobby_EventScript_RulesLevel
	case 1, FallarborTown_BattleTentLobby_EventScript_RulesBattle
	case 2, FallarborTown_BattleTentLobby_EventScript_RulesMind
	case 3, FallarborTown_BattleTentLobby_EventScript_RulesSkill
	case 4, FallarborTown_BattleTentLobby_EventScript_RulesBody
	case 5, FallarborTown_BattleTentLobby_EventScript_ExitRules
	case MULTI_B_PRESSED, FallarborTown_BattleTentLobby_EventScript_ExitRules
	end

FallarborTown_BattleTentLobby_EventScript_RulesLevel::
	msgbox BattleTentLobby_Text_ExplainLevelRules, MSGBOX_DEFAULT
	goto FallarborTown_BattleTentLobby_EventScript_ReadRulesBoard
	end

FallarborTown_BattleTentLobby_EventScript_RulesBattle::
	msgbox BattleFrontier_BattleArenaLobby_Text_ExplainBattleRules, MSGBOX_DEFAULT
	goto FallarborTown_BattleTentLobby_EventScript_ReadRulesBoard
	end

FallarborTown_BattleTentLobby_EventScript_RulesMind::
	msgbox BattleFrontier_BattleArenaLobby_Text_ExplainMindRules, MSGBOX_DEFAULT
	goto FallarborTown_BattleTentLobby_EventScript_ReadRulesBoard
	end

FallarborTown_BattleTentLobby_EventScript_RulesSkill::
	msgbox BattleFrontier_BattleArenaLobby_Text_ExplainSkillRules, MSGBOX_DEFAULT
	goto FallarborTown_BattleTentLobby_EventScript_ReadRulesBoard
	end

FallarborTown_BattleTentLobby_EventScript_RulesBody::
	msgbox BattleFrontier_BattleArenaLobby_Text_ExplainBodyRules, MSGBOX_DEFAULT
	goto FallarborTown_BattleTentLobby_EventScript_ReadRulesBoard
	end

FallarborTown_BattleTentLobby_EventScript_ExitRules::
	releaseall
	end




FallarborTown_BattleTentLobby_Text_ScottLookingForSomeone:
	.string "SCOTT: Hi, {PLAYER}{KUN}!\n"
	.string "So you came out to this BATTLE TENT!\p"
	.string "The people in these parts tend to be\n"
	.string "easygoing and laid-back.\p"
	.string "But, you see, what I'm looking for are\n"
	.string "people with…\p"
	.string "How should I say this?\p"
	.string "Someone bursting with the desire\n"
	.string "and the drive to win.\p"
	.string "If there were a TRAINER like that,\n"
	.string "I'd immediately…\p"
	.string "Whoops! Never mind!\n"
	.string "Keep working at it!$"

FallarborTown_BattleTentLobby_Text_ScottMakeChallenge:
	.string "SCOTT: Instead of wasting your\n"
	.string "time with the likes of me, why not\l"
	.string "make a challenge?$"

