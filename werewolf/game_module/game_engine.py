# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-10-16 14:41:14
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 17:30:29

from flask import request, current_app
from flask_login import current_user
import json
from werewolf.utils.json_utils import JsonHook, ExtendJSONEncoder
from werewolf.utils.enums import GameStatus, RoleType, TurnStep, CaptainMode
from werewolf.utils.game_message import GameMessage
from werewolf.game_module.game import Game, GameTable
from collections import Counter
import random


def take_action() -> (bool, GameMessage):
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
            return False, GameMessage('CANNOT_START')

        cards = list(Counter(game.card_dict).elements())
        random.shuffle(cards)
        for r, c in zip(game.roles, cards):
            r.role_type = c
            r.prepare()
            r.commit()

        game.status = GameStatus.NIGHT
        game.go_next_step()

    me.commit()
    role.commit()
    game.commit()


def _next_step(turn_dict, card_dict, captain_mode) -> (dict, GameStatus):
    if turn_dict is None:
        turn = _reset_turn(1, card_dict, captain_mode)
        return turn, GameStatus.NIGHT


def _reset_turn(day, card_dict, captain_mode):
    steps = []
    if day == 1 and RoleType.THIEF in card_dict:
        pass
    if day == 1 and RoleType.CUPID in card_dict:
        pass
    # TODO: 恋人互相确认身份
    steps.append(RoleType.ALL_WOLF)
    steps.append(RoleType.SEER)
    steps.append(RoleType.WITCH)
    steps.append(RoleType.SAVIOR)
    steps.append(TurnStep.CHECK_VICTORY)
    steps.append(TurnStep.TURN_DAY)
    if day == 1 and captain_mode is CaptainMode.WITH_CAPTAIN:
        steps.append(TurnStep.ELECT)
        steps.append(TurnStep.TALK)
        steps.append(TurnStep.VOTE_FOR_CAPTAIN)
    steps.append(TurnStep.ANNOUNCE_AND_TALK)

    return {'day': day,
            'current_step': 0,
            'steps': steps,
            'repeat': 0
            }
