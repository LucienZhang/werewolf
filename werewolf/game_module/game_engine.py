# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-10-16 14:41:14
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 17:30:29

from flask import request, current_app
from flask_login import current_user
import json
# from werewolf.utils.json_utils import JsonHook, ExtendedJSONEncoder
# from werewolf.utils.enums import GameStatus, RoleType, TurnStep, CaptainMode
# from werewolf.utils.game_message import GameMessage
from werewolf.utils.enums import GameEnum
from werewolf.game_module.game import Game, GameTable
from collections import Counter
import random


def take_action() -> (bool, GameEnum):
    # /action?op=start
    # /action?op=see&target=1
    me = current_user
    role = current_user.role
    game = current_user.game
    op = request.args.get('op')
    if op == 'start':
        # TODO: with lock!
        positions = set()
        for r in game.roles:
            positions.add(r.position)
        if len(positions) != game.get_seat_num():
            return False, GameEnum('GAME_MESSAGE_CANNOT_START')

        cards = game.cards.copy()
        random.shuffle(cards)
        for r, c in zip(game.roles, cards):
            r.role_type = c
            r.prepare()
            r.commit()

        game.status = GameEnum.GAME_STATUS_NIGHT
        game.go_next_step()

    me.commit()
    role.commit()
    game.commit()


def _next_step(turn_dict, cards, captain_mode) -> (dict, GameEnum):
    if turn_dict is None:
        turn = _reset_turn(1, cards, captain_mode)
        return turn, GameEnum.GAME_STATUS_NIGHT


def _reset_turn(day, cards, captain_mode):
    steps = []
    if day == 1 and GameEnum.ROLE_TYPE_THIEF in cards:
        pass
    if day == 1 and GameEnum.ROLE_TYPE_CUPID in cards:
        pass
    # TODO: 恋人互相确认身份
    steps.append(GameEnum.ROLE_TYPE_ALL_WOLF)
    steps.append(GameEnum.ROLE_TYPE_SEER)
    steps.append(GameEnum.ROLE_TYPE_WITCH)
    steps.append(GameEnum.ROLE_TYPE_SAVIOR)
    steps.append(GameEnum.TURN_STEP_CHECK_VICTORY)
    steps.append(GameEnum.TURN_STEP_TURN_DAY)
    if day == 1 and captain_mode is GameEnum.CAPTAIN_MODE_WITH_CAPTAIN:
        steps.append(GameEnum.TURN_STEP_ELECT)
        steps.append(GameEnum.TURN_STEP_TALK)
        steps.append(GameEnum.TURN_STEP_VOTE_FOR_CAPTAIN)
    steps.append(GameEnum.TURN_STEP_ANNOUNCE_AND_TALK)

    return {'day': day,
            'current_step': 0,
            'steps': steps,
            'repeat': 0
            }
