from datetime import datetime, timedelta
import json
import random
from flask import request
from flask_login import current_user
from werewolf.database import db, User, Game, Role
from werewolf.utils.enums import GameEnum
from werewolf.utils.json_utils import json_hook, ExtendedJSONEncoder
from werewolf.utils.publisher import publish_info


def setup_game() -> dict:
    victory_mode = GameEnum['VICTORY_MODE_{}'.format(
        request.form['victoryMode'].upper())]
    captain_mode = GameEnum['CAPTAIN_MODE_{}'.format(
        request.form['captainMode'].upper())]
    witch_mode = GameEnum['WITCH_MODE_{}'.format(
        request.form['witchMode'].upper())]
    villager_cnt = int(request.form['villager'])
    normal_wolf_cnt = int(request.form['normal_wolf'])
    cards = [GameEnum.ROLE_TYPE_VILLAGER] * villager_cnt + [GameEnum.ROLE_TYPE_NORMAL_WOLF] * normal_wolf_cnt

    single_roles = request.form.getlist('single_roles')
    for r in single_roles:
        cards.append(GameEnum[f'ROLE_TYPE_{r.upper()}'])

    new_game = Game(host_uid=current_user.uid,
                    victory_mode=victory_mode,
                    captain_mode=captain_mode,
                    witch_mode=witch_mode,
                    wolf_mode=_get_wolf_mode_by_cards(cards),
                    cards=cards,
                    )
    _init_game(new_game)
    db.session.add(new_game)
    db.session.commit()

    return GameEnum.OK.digest(gid=new_game.gid)


def join_game() -> dict:
    gid = int(request.args['gid'])
    with Game.query.with_for_update().get(gid) as game:
        if not game or datetime.utcnow() > game.end_time:
            return GameEnum.GAME_MESSAGE_GAME_NOT_EXIST.digest()
        if game.status is not GameEnum.GAME_STATUS_WAIT_TO_START:
            return GameEnum.GAME_MESSAGE_ALREADY_STARTED.digest()
        if current_user.uid in game.players:
            current_user.gid = gid
            db.session.add(current_user)
            db.session.commit()
            return GameEnum.GAME_MESSAGE_ALREADY_IN.digest()
        if len(game.players) >= game.get_seats_cnt():
            return GameEnum.GAME_MESSAGE_GAME_FULL.digest()

        # fine to join the game
        game.players.append(current_user.uid)
        current_user.gid = gid
        current_role = Role.query.get(current_user.uid)
        current_role.gid = gid
        current_role.reset()
        db.session.commit()
        return GameEnum.OK.digest()


def quit_game() -> dict:
    gid = current_user.gid
    with Game.query.with_for_update().get(gid) as game:
        if not game or datetime.utcnow() > game.end_time:
            return GameEnum.GAME_MESSAGE_NOT_IN_GAME.digest()
        if game.status is not GameEnum.GAME_STATUS_WAIT_TO_START:
            pass  # todo easy to quit??
        if current_user.uid not in game.players:
            return GameEnum.GAME_MESSAGE_NOT_IN_GAME.digest()
        game.players.remove(current_user.uid)
        current_user.gid = -1
        current_role = Role.query.get(current_user.uid)
        current_role.gid = -1
        current_role.reset()
        db.session.commit()
        return GameEnum.OK.digest()


def deal() -> dict:
    with Game.query.with_for_update().get(current_user.gid) as game:
        if not game or datetime.utcnow() > game.end_time:
            return GameEnum.GAME_MESSAGE_CANNOT_START.digest()
        if game.status is not GameEnum.GAME_STATUS_WAIT_TO_START:
            return GameEnum.GAME_MESSAGE_CANNOT_START.digest()
        players_cnt = len(game.players)
        if players_cnt != game.get_seats_cnt():
            return GameEnum.GAME_MESSAGE_CANNOT_START.digest()
        players = Role.query.filter(Role.gid == game.gid).limit(players_cnt).all()
        if len(players) != players_cnt:
            return GameEnum.GAME_MESSAGE_CANNOT_START.digest()
        for p in players:
            if p.uid not in game.players:
                return GameEnum.GAME_MESSAGE_CANNOT_START.digest()
        if set([p.position for p in players]) != set(range(1, players_cnt + 1)):
            return GameEnum.GAME_MESSAGE_CANNOT_START.digest()

        # fine to deal
        game.status = GameEnum.GAME_STATUS_READY
        players.sort(key=lambda p: p.position)
        game.players = [p.uid for p in players]
        cards = game.cards.copy()
        random.shuffle(cards)
        for p, c in zip(players, cards):
            p.role_type = c
            p.prepare(game.captain_mode)
        publish_info(game.gid, json.dumps({'cards': True}))
        return GameEnum.OK.digest()


def get_game_info() -> dict:
    game = Game.query.get(current_user.gid)
    if not game:
        return GameEnum.GAME_MESSAGE_NOT_IN_GAME.digest()
    all_players = Role.query.filter(Role.gid == game.gid).limit(len(game.players)).all()
    role = Role.query.get(current_user.uid)
    return GameEnum.OK.digest(
        game={
            'players': {p.position: [p.nickname, p.avatar] for p in all_players},
            'status': [game.status.name, game.status.label],
        },
        role={
            'role_type': role.role_type.label,
            'skills': [sk.label for sk in role.skills],
        })


def _init_game(game):
    game.status = GameEnum.GAME_STATUS_WAIT_TO_START
    game.end_time = datetime.utcnow() + timedelta(days=1)
    game.days = 0
    game.now_index = -1
    game.step_cnt = 0
    game.steps = []
    game.history = {}
    game.captain_uid = -1
    game.players = []


def _get_wolf_mode_by_cards(cards):
    # WOLF_MODE_FIRST if there is no thrid party, else WOLF_MODE_ALL
    if GameEnum.ROLE_TYPE_CUPID in cards:
        return GameEnum.WOLF_MODE_ALL
    else:
        return GameEnum.WOLF_MODE_FIRST


# def _reset_step_list(game) -> list:
#     # ,day, cards, captain_mode
#     step_list = []
#     step_list.append(GameEnum.TURN_STEP_TURN_NIGHT)
#     if day == 1 and GameEnum.ROLE_TYPE_THIEF in cards:
#         pass
#     if day == 1 and GameEnum.ROLE_TYPE_CUPID in cards:
#         pass
#     # TODO: 恋人互相确认身份
#     step_list.append(GameEnum.ROLE_TYPE_ALL_WOLF)
#     if GameEnum.ROLE_TYPE_SEER in cards:
#         step_list.append(GameEnum.ROLE_TYPE_SEER)
#     if GameEnum.ROLE_TYPE_WITCH in cards:
#         step_list.append(GameEnum.ROLE_TYPE_WITCH)
#     if GameEnum.ROLE_TYPE_SAVIOR in cards:
#         step_list.append(GameEnum.ROLE_TYPE_SAVIOR)
#     step_list.append(GameEnum.TURN_STEP_TURN_DAY)
#     if day == 1 and captain_mode is GameEnum.CAPTAIN_MODE_WITH_CAPTAIN:
#         step_list.append(GameEnum.TURN_STEP_ELECT)
#         step_list.append(GameEnum.TURN_STEP_ELECT_TALK)
#         step_list.append(GameEnum.TURN_STEP_CAPTAIN_VOTE)
#     step_list.append(GameEnum.TURN_STEP_ANNOUNCE)
#     step_list.append(GameEnum.TURN_STEP_TALK)
#     step_list.append(GameEnum.TURN_STEP_VOTE)
#     step_list.append(GameEnum.TURN_STEP_LAST_WORDS)

#     # step_list.append(GameEnum.TURN_STEP_TURN_NIGHT)

#     return step_list
