from flask import request, current_app
from flask_login import current_user
import json
from werewolf.utils.enums import GameEnum
from werewolf.game_module.game import Game, GameTable
from collections import Counter
import random
from werewolf.utils.json_utils import response
from werewolf.utils.scheduler import scheduler
from werewolf.utils.publisher import publish_info
import datetime


def take_action() -> str:  # return json to user
    # /action?op=start
    # /action?op=see&target=1
    me = current_user
    op = request.args.get('op')
    if op == 'start':
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
            publish_info(game.gid, json.dumps(
                {'seats': {str(role.position): role.name for role in game.roles if role.position > 0}}))
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
            target_role = game.get_role_by_pos(target)
            if not target_role.alive:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            history['discover'] = target
            return response(True, game.get_role_by_pos(target).group_type.message)
    elif op == 'elixir':
        with Game.get_game_by_gid(me.gid, lock=True, load_roles=True) as game:
            history = game.history
            my_role = game.get_role_by_uid(me.uid)
            if game.status != GameEnum.ROLE_TYPE_WITCH or my_role.role_type != GameEnum.ROLE_TYPE_WITCH:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            if my_role.args['elixir'] < 1:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            if history['elixir'] or history['toxic'] != GameEnum.TARGET_NOT_ACTED:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            if history['wolf_kill_decision'] is GameEnum.TARGET_NO_ONE:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            history['elixir'] = True
            my_role.args['elixir'] -= 1
            my_role.commit()
            return response(True)
    elif op == 'toxic':
        target = request.args.get('target')
        with Game.get_game_by_gid(me.gid, lock=True, load_roles=True) as game:
            history = game.history
            my_role = game.get_role_by_uid(me.uid)
            if game.status != GameEnum.ROLE_TYPE_WITCH or my_role.role_type != GameEnum.ROLE_TYPE_WITCH:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            if my_role.args['toxic'] < 1:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            if history['elixir'] or history['toxic'] != GameEnum.TARGET_NOT_ACTED:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            target_role = game.get_role_by_pos(target)
            if not target_role.alive:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            history['toxic'] = target
            my_role.args['toxic'] -= 1
            my_role.commit()
            return response(True)
    elif op == 'guard':
        target = request.args.get('target')
        with Game.get_game_by_gid(me.gid, lock=True, load_roles=True) as game:
            history = game.history
            my_role = game.get_role_by_uid(me.uid)
            if game.status != GameEnum.ROLE_TYPE_SAVIOR or my_role.role_type != GameEnum.ROLE_TYPE_SAVIOR:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            if my_role.args['guard'] != GameEnum.TARGET_NO_ONE and my_role.args['guard'] == target:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            if history['guard'] != GameEnum.TARGET_NOT_ACTED:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            target_role = game.get_role_by_pos(target)
            if not target_role.alive:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            history['guard'] = target
            my_role.args['guard'] = target
            my_role.commit()
            return response(True)
    elif op == 'shoot':
        target = request.args.get('target')
        with Game.get_game_by_gid(me.gid, lock=True, load_roles=True) as game:
            history = game.history
            my_role = game.get_role_by_uid(me.uid)
            now = game.current_step()
            if not (now is GameEnum.GAME_STATUS_SHOOT_AVAILABLE and me.uid in now.args):
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            if not my_role.args['shootable']:
                return response(False, GameEnum.GAME_MESSAGE_CANNOT_ACT.message)
            kill(my_role, target)
            return response(True)
    else:
        return response(False, GameEnum.GAME_MESSAGE_UNKNOWN_OP.message)


def kill(by, target):
    pass
