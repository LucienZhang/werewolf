# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-10-16 14:41:14
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 17:30:29

from flask import request, current_app
from flask_login import current_user
import json
from werewolf.utils.enums import GameEnum
from werewolf.game_module.game import Game, GameTable
from collections import Counter
import random
from werewolf.utils.json_utils import response
from werewolf.utils.scheduler import scheduler
import datetime


def take_action() -> str:  # return json to user
    # /action?op=start
    # /action?op=see&target=1
    me = current_user
    op = request.args.get('op')
    if op == 'start':
        # TODO: with lock!
        with Game.get_game_by_gid(me.gid, lock=True, load_roles=True) as game:
            positions = set()
            for r in game.roles:
                positions.add(r.position)
            if len(positions) != game.get_seat_num():
                return response(False, GameEnum('GAME_MESSAGE_CANNOT_START').message)

            cards = game.cards.copy()
            random.shuffle(cards)
            for r, c in zip(game.roles, cards):
                r.role_type = c
                r.prepare()
                r.commit()
            game.status = GameEnum.GAME_STATUS_NIGHT
            game.go_next_step()
            return response(True)
    elif op == 'wolf_kill':
        target = request.args.get('target')
        with Game.get_game_by_gid(me.gid, lock=True, load_roles=True) as game:
            history = game.history
            my_role = game.get_role_by_uid(me.uid)
            if game.status != GameEnum.ROLE_TYPE_ALL_WOLF or GameEnum.ROLE_TYPE_ALL_WOLF not in my_role.tags:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            if my_role.position not in history['wolf_kill'] or \
                    history['wolf_kill'][my_role.position] != GameEnum.TARGET_NOT_ACTED:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            history['wolf_kill'][my_role.position] = target
            if all([t != GameEnum.TARGET_NOT_ACTED for t in history['wolf_kill'].values()]):
                game.go_next_step()
            return response(True)
    elif op == 'sit':
        position = request.args.get('position')
        with Game.get_game_by_gid(me.gid, lock=True, load_roles=True) as game:
            if game.status != GameEnum.GAME_STATUS_WAIT_TO_START:
                return response(False, GameEnum('GAME_MESSAGE_ALREADY_STARTED').message)
            if game.get_role_by_pos(position):
                return response(False, GameEnum('GAME_MESSAGE_POSITION_OCCUPIED').message)
            my_role = game.get_role_by_uid(me.uid)
            if not my_role:
                return response(False, GameEnum('GAME_MESSAGE_ROLE_NOT_EXIST').message)
            my_role.position = position
            my_role.commit()
            # todo: publish position info
            return response(True)
    elif op == 'discover':
        target = request.args.get('target')
        with Game.get_game_by_gid(me.gid, lock=True, load_roles=True) as game:
            history = game.history
            my_role = game.get_role_by_uid(me.uid)
            if game.status != GameEnum.ROLE_TYPE_SEER or my_role.role_type != GameEnum.ROLE_TYPE_SEER:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            if history['discover'] != GameEnum.TARGET_NOT_ACTED:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            history['discover'] = target
            return response(True, game.get_role_by_pos(target).group_type.message)
    elif op == 'elixir':
        pass
    elif op == 'toxic':
        pass
    elif op == 'guard':
        pass
    elif op == 'shoot':
        pass
    else:
        return response(False, GameEnum.GAME_MESSAGE_UNKNOWN_OP.message)

#
#
# def _next_step(turn_dict, cards, captain_mode) -> (dict, GameEnum):
#     if turn_dict is None:
#         turn = _reset_turn(1, cards, captain_mode)
#         return turn, GameEnum.GAME_STATUS_NIGHT
#
#
# def _reset_turn(day, cards, captain_mode):
#     steps = []
#     if day == 1 and GameEnum.ROLE_TYPE_THIEF in cards:
#         pass
#     if day == 1 and GameEnum.ROLE_TYPE_CUPID in cards:
#         pass
#     # TODO: 恋人互相确认身份
#     steps.append(GameEnum.ROLE_TYPE_ALL_WOLF)
#     steps.append(GameEnum.ROLE_TYPE_SEER)
#     steps.append(GameEnum.ROLE_TYPE_WITCH)
#     steps.append(GameEnum.ROLE_TYPE_SAVIOR)
#     steps.append(GameEnum.TURN_STEP_CHECK_VICTORY)
#     steps.append(GameEnum.TURN_STEP_TURN_DAY)
#     if day == 1 and captain_mode is GameEnum.CAPTAIN_MODE_WITH_CAPTAIN:
#         steps.append(GameEnum.TURN_STEP_ELECT)
#         steps.append(GameEnum.TURN_STEP_TALK)
#         steps.append(GameEnum.TURN_STEP_VOTE_FOR_CAPTAIN)
#     steps.append(GameEnum.TURN_STEP_ANNOUNCE_AND_TALK)
#
#     return {'day': day,
#             'current_step': 0,
#             'steps': steps,
#             'repeat': 0
#             }
