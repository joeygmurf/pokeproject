Route114_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, Route114_OnTransition
	map_script MAP_SCRIPT_ON_LOAD, Route114_OnLoad
	map_script MAP_SCRIPT_ON_FRAME_TABLE, Route114_OnFrame
	.byte 0

Route114_OnTransition:
	call Route114_EventScript_SetUpCutTutor
	call_if_eq VAR_SHOULD_END_ABNORMAL_WEATHER, 1, AbnormalWeather_EventScript_HideMapNamePopup
	call_if_eq VAR_ABNORMAL_WEATHER_LOCATION, ABNORMAL_WEATHER_ROUTE_114_NORTH, AbnormalWeather_StartGroudonWeather
	call_if_eq VAR_ABNORMAL_WEATHER_LOCATION, ABNORMAL_WEATHER_ROUTE_114_SOUTH, AbnormalWeather_StartGroudonWeather
	end

Route114_OnLoad:
	call_if_eq VAR_ABNORMAL_WEATHER_LOCATION, ABNORMAL_WEATHER_ROUTE_114_NORTH, AbnormalWeather_EventScript_PlaceTilesRoute114North
	call_if_eq VAR_ABNORMAL_WEATHER_LOCATION, ABNORMAL_WEATHER_ROUTE_114_SOUTH, AbnormalWeather_EventScript_PlaceTilesRoute114South
	end

Route114_OnFrame:
	map_script_2 VAR_SHOULD_END_ABNORMAL_WEATHER, 1, AbnormalWeather_EventScript_EndEventAndCleanup_1
	.2byte 0

@ The Cut gate before the bridge. The three cuttable trees at (20..22,15) are a
@ verified cut point: the channel either side is water, so with them standing
@ only 194 tiles are reachable from the north and Meteor Falls is not among
@ them. They carry permanent flags instead of vanilla's FLAG_TEMP_11, so they
@ stay cut once cut.
@
@ He disappears once Cut has been handed over AND Lucy is beaten. Both halves
@ matter: hiding him on the badge alone would strand a player who reached
@ Fallarbor by another route and never collected the HM.
Route114_EventScript_SetUpCutTutor::
	goto_if_unset FLAG_RECEIVED_HM_CUT, Route114_EventScript_ShowCutTutor
	goto_if_unset FLAG_DEFEATED_FALLARBOR_GYM, Route114_EventScript_ShowCutTutor
	setflag FLAG_HIDE_ROUTE114_CUT_TUTOR
	return

Route114_EventScript_ShowCutTutor::
	clearflag FLAG_HIDE_ROUTE114_CUT_TUTOR
	return

Route114_EventScript_CutTutor::
	lock
	faceplayer
	goto_if_set FLAG_RECEIVED_HM_CUT, Route114_EventScript_CutTutorBeatLucyYet
	msgbox Route114_Text_CutTutorTakeThis, MSGBOX_DEFAULT
	giveitem ITEM_HM_CUT
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_BagIsFull
	setflag FLAG_RECEIVED_HM_CUT
	msgbox Route114_Text_CutTutorNeedLucy, MSGBOX_DEFAULT
	release
	end

Route114_EventScript_CutTutorBeatLucyYet::
	msgbox Route114_Text_CutTutorBeatLucyYet, MSGBOX_DEFAULT
	release
	end

Route114_Text_CutTutorTakeThis:
	.string "Hi there! If you ever run into trees\n"
	.string "like this, you can have a POKéMON\l"
	.string "cut them down!\p"
	.string "……\p"
	.string "Oh? You don't have HM CUT?\n"
	.string "I have an extra one you can take,\l"
	.string "here you go!$"

Route114_Text_CutTutorNeedLucy:
	.string "You need to beat LUCY in FALLARBOR\n"
	.string "before you can have a POKéMON use\l"
	.string "it out of battle.$"

Route114_Text_CutTutorBeatLucyYet:
	.string "Hey there! Beat LUCY yet?\n"
	.string "You'll need to before passing\l"
	.string "through here.$"

@ Aqua Admins Matt and Shelly, fought as one double battle against two separate
@ trainers. They stand on (8,68) and (9,68), which a flood fill confirms are the
@ only two walkable tiles into the Meteor Falls corridor - so they are removed
@ on a win, or they would wall it off for good.
@
@ TODO: placeholder dialogue, pending the user's own lines.
Route114_EventScript_AquaAdmins::
	lock
	faceplayer
	msgbox Route114_Text_AquaAdminsIntro, MSGBOX_DEFAULT
	closemessage
	trainerbattle OBJ_ID_NONE, TRAINER_MATT_ROUTE114, NULL, Route114_Text_MattDefeat, NULL, OBJ_ID_NONE, TRAINER_SHELLY_ROUTE114, NULL, Route114_Text_ShellyDefeat, NULL, NULL, NULL, FALSE, TRUE, FALSE, FALSE, TRUE, TRUE, FALSE, FALSE
	msgbox Route114_Text_AquaAdminsDefeated, MSGBOX_DEFAULT
	closemessage
	setflag FLAG_CAP_AQUA_ADMINS
	removeobject LOCALID_ROUTE114_MATT
	removeobject LOCALID_ROUTE114_SHELLY
	call Common_EventScript_LevelCapIncreased
	release
	end

Route114_Text_AquaAdminsIntro:
	.string "MATT: Far enough, kid.\n"
	.string "Nobody goes up to METEOR FALLS.\p"
	.string "SHELLY: Both of us, then.\n"
	.string "Let's not drag this out.$"

Route114_Text_MattDefeat:
	.string "No way…$"

Route114_Text_ShellyDefeat:
	.string "Hmph. Not bad.$"

Route114_Text_AquaAdminsDefeated:
	.string "SHELLY: Fine. Go and look.\n"
	.string "It won't change anything.$"

Route114_EventScript_Man::
	lock
	faceplayer
	dotimebasedevents
	goto_if_set FLAG_DAILY_ROUTE_114_RECEIVED_BERRY, Route114_EventScript_ReceivedBerry
	msgbox Route114_Text_LoveUsingBerryCrushShareBerry, MSGBOX_DEFAULT
	giverandomberry BERRY_ID_RAZZ, BERRY_ID_PINAP
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull
	setflag FLAG_DAILY_ROUTE_114_RECEIVED_BERRY
	msgbox Route114_Text_TryBerryCrushWithFriends, MSGBOX_DEFAULT
	release
	end

Route114_EventScript_ReceivedBerry::
	msgbox Route114_Text_FunToThinkAboutBerries, MSGBOX_DEFAULT
	release
	end

Route114_EventScript_RoarGentleman::
	lock
	faceplayer
	goto_if_set FLAG_RECEIVED_TM_ROAR, Route114_EventScript_ReceivedRoar
	msgbox Route114_Text_AllMyMonDoesIsRoarTakeThis, MSGBOX_DEFAULT
	giveitem ITEM_TM_ROAR
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull
	setflag FLAG_RECEIVED_TM_ROAR
	msgbox Route114_Text_ExplainRoar, MSGBOX_DEFAULT
	release
	end

Route114_EventScript_ReceivedRoar::
	msgbox Route114_Text_ExplainRoar, MSGBOX_DEFAULT
	release
	end

Route114_EventScript_Poochyena::
	lock
	faceplayer
	waitse
	playmoncry SPECIES_POOCHYENA, CRY_MODE_ENCOUNTER
	msgbox Route114_Text_Poochyena, MSGBOX_DEFAULT
	waitmoncry
	release
	end

Route114_EventScript_MeteorFallsSign::
	msgbox Route114_Text_MeteorFallsSign, MSGBOX_SIGN
	end

Route114_EventScript_FossilManiacsHouseSign::
	msgbox Route114_Text_FossilManiacsHouseSign, MSGBOX_SIGN
	end

Route114_EventScript_LanettesHouseSign::
	msgbox Route114_Text_LanettesHouse, MSGBOX_SIGN
	end

Route114_EventScript_Lenny::
	trainerbattle_single TRAINER_LENNY, Route114_Text_LennyIntro, Route114_Text_LennyDefeat
	msgbox Route114_Text_LennyPostBattle, MSGBOX_AUTOCLOSE
	end

Route114_EventScript_Lucas::
	trainerbattle_single TRAINER_LUCAS_1, Route114_Text_LucasIntro, Route114_Text_LucasDefeat
	msgbox Route114_Text_LucasPostBattle, MSGBOX_AUTOCLOSE
	end

Route114_EventScript_Shane::
	trainerbattle_single TRAINER_SHANE, Route114_Text_ShaneIntro, Route114_Text_ShaneDefeat
	msgbox Route114_Text_ShanePostBattle, MSGBOX_AUTOCLOSE
	end

Route114_EventScript_Nancy::
	trainerbattle_single TRAINER_NANCY, Route114_Text_NancyIntro, Route114_Text_NancyDefeat
	msgbox Route114_Text_NancyPostBattle, MSGBOX_AUTOCLOSE
	end

Route114_EventScript_Steve::
	trainerbattle_single TRAINER_STEVE_1, Route114_Text_SteveIntro, Route114_Text_SteveDefeat, Route114_EventScript_RegisterSteve
	specialvar VAR_RESULT, ShouldTryRematchBattle
	goto_if_eq VAR_RESULT, TRUE, Route114_EventScript_RematchSteve
	msgbox Route114_Text_StevePostBattle, MSGBOX_DEFAULT
	release
	end

Route114_EventScript_RegisterSteve::
	special PlayerFaceTrainerAfterBattle
	waitmovement 0
	msgbox Route114_Text_SteveRegister, MSGBOX_DEFAULT
	register_matchcall TRAINER_STEVE_1
	release
	end

Route114_EventScript_RematchSteve::
	trainerbattle_rematch TRAINER_STEVE_1, Route114_Text_SteveRematchIntro, Route114_Text_SteveRematchDefeat
	msgbox Route114_Text_StevePostRematch, MSGBOX_AUTOCLOSE
	end

Route114_EventScript_Bernie::
	trainerbattle_single TRAINER_BERNIE_1, Route114_Text_BernieIntro, Route114_Text_BernieDefeat, Route114_EventScript_RegisterBernie
	specialvar VAR_RESULT, ShouldTryRematchBattle
	goto_if_eq VAR_RESULT, TRUE, Route114_EventScript_RematchBernie
	msgbox Route114_Text_BerniePostBattle, MSGBOX_DEFAULT
	release
	end

Route114_EventScript_RegisterBernie::
	special PlayerFaceTrainerAfterBattle
	waitmovement 0
	msgbox Route114_Text_BernieRegister, MSGBOX_DEFAULT
	register_matchcall TRAINER_BERNIE_1
	release
	end

Route114_EventScript_RematchBernie::
	trainerbattle_rematch TRAINER_BERNIE_1, Route114_Text_BernieRematchIntro, Route114_Text_BernieRematchDefeat
	msgbox Route114_Text_BerniePostRematch, MSGBOX_AUTOCLOSE
	end


Route114_EventScript_Nolan::
	trainerbattle_single TRAINER_NOLAN, Route114_Text_NolanIntro, Route114_Text_NolanDefeat
	msgbox Route114_Text_NolanPostBattle, MSGBOX_AUTOCLOSE
	end

Route114_EventScript_Tyra::
	trainerbattle_double TRAINER_TYRA_AND_IVY, Route114_Text_TyraIntro, Route114_Text_TyraDefeat, Route114_Text_TyraNotEnoughMons
	msgbox Route114_Text_TyraPostBattle, MSGBOX_AUTOCLOSE
	end

Route114_EventScript_Ivy::
	trainerbattle_double TRAINER_TYRA_AND_IVY, Route114_Text_IvyIntro, Route114_Text_IvyDefeat, Route114_Text_IvyNotEnoughMons
	msgbox Route114_Text_IvyPostBattle, MSGBOX_AUTOCLOSE
	end

Route114_EventScript_Angelina::
	trainerbattle_single TRAINER_ANGELINA, Route114_Text_AngelinaIntro, Route114_Text_AngelinaDefeat
	msgbox Route114_Text_AngelinaPostBattle, MSGBOX_AUTOCLOSE
	end

Route114_EventScript_Charlotte::
	trainerbattle_single TRAINER_CHARLOTTE, Route114_Text_CharlotteIntro, Route114_Text_CharlotteDefeat
	msgbox Route114_Text_CharlottePostBattle, MSGBOX_AUTOCLOSE
	end

Route114_EventScript_Kai::
	trainerbattle_single TRAINER_KAI, Route114_Text_KaiIntro, Route114_Text_KaiDefeat
	msgbox Route114_Text_KaiPostBattle, MSGBOX_AUTOCLOSE
	end

Route114_Text_AllMyMonDoesIsRoarTakeThis:
	.string "All my POKéMON does is ROAR…\n"
	.string "No one dares to come near me…\p"
	.string "Sigh… If you would, please take\n"
	.string "this TM away…$"

Route114_Text_ExplainRoar:
	.string "TM05 contains ROAR.\n"
	.string "A ROAR sends POKéMON scurrying.$"

Route114_Text_Poochyena:
	.string "Bow! Bowwow!$"

Route114_Text_MeteorFallsSign:
	.string "METEOR FALLS\n"
	.string "RUSTBORO CITY THROUGH HERE$"

Route114_Text_FossilManiacsHouseSign:
	.string "FOSSIL MANIAC'S HOUSE\n"
	.string "“Fossils gratefully accepted!”$"

Route114_Text_LanettesHouse:
	.string "LANETTE'S HOUSE$"

