from datetime import datetime, timedelta
import json
import random
from flask import request, current_app
from flask_login import current_user
from werewolf.database import db, User, Game, Role
from werewolf.utils.enums import GameEnum
from werewolf.utils.json_utils import json_hook, ExtendedJSONEncoder
from werewolf.utils.publisher import publish_info, publish_history
from werewolf.game_engine.step_processor import StepProcessor


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
    StepProcessor.init_game(new_game)
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
    if gid < 0:
        return GameEnum.GAME_MESSAGE_NOT_IN_GAME.digest()
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
            'role_type': [role.role_type.name, role.role_type.label],
            'skills': [[sk.name, sk.label] for sk in role.skills],
        })


def sit()->dict:
    position = int(request.args.get('position'))
    game = Game.query.get(current_user.gid)
    if game.status is not GameEnum.GAME_STATUS_WAIT_TO_START:
        return GameEnum.GAME_MESSAGE_ALREADY_STARTED.digest()
    my_role = Role.query.get(current_user.uid)
    my_role.position = position
    db.session.commit()
    all_players = Role.query.filter(Role.gid == game.gid).limit(len(game.players)).all()
    publish_info(game.gid, json.dumps(
        GameEnum.OK.digest(
            seats={p.position: [p.nickname, p.avatar] for p in all_players},
        )
    ))
    return GameEnum.OK.digest()


def next_step()->dict:
    with Game.query.with_for_update().get(current_user.gid) as game:
        if game.status not in [GameEnum.GAME_STATUS_READY, GameEnum.GAME_STATUS_DAY]:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        return StepProcessor.move_on(game)


def vote()->dict:
    target = int(request.args.get('target'))
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
    with Game.query.with_for_update().get(current_user.gid) as game:
        if not my_role.voteable or my_role.position not in game.history['voter_votee'][0]:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if target != GameEnum.TARGET_NO_ONE.value and target not in game.history['voter_votee'][1]:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        now = StepProcessor.current_step(game)
        if now in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_ELECT_VOTE]:
            game.history['vote_result'][my_role.position] = target
            game.history.changed()
            if target > 0:
                return GameEnum.OK.digest(result=f'你投了{target}号玩家')
            else:
                return GameEnum.OK.digest(result=f'你弃票了')
        elif now in [GameEnum.TURN_STEP_PK_VOTE, GameEnum.TURN_STEP_ELECT_PK_VOTE]:
            if target == GameEnum.TARGET_NO_ONE.value:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            else:
                game.history['vote_result'][my_role.position] = target
                game.history.changed()
                if target > 0:
                    return GameEnum.OK.digest(result=f'你投了{target}号玩家')
                else:
                    return GameEnum.OK.digest(result=f'你弃票了')
        else:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()


def handover()->dict:
    target = int(request.args.get('target'))
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        current_app.logger.info('my_role is not alive')
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
    with Game.query.with_for_update().get(current_user.gid) as game:
        now = StepProcessor.current_step(game)
        if now is not GameEnum.TURN_STEP_LAST_WORDS:
            current_app.logger.info(f'wrong now step:{now.label}')
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if str(my_role.position) not in game.history['dying']:
            current_app.logger.info(f'not in dying: my position={my_role.position},dying={game.history["dying"]}')
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if game.captain_pos != my_role.position:
            current_app.logger.info(f'I am not captain, my position={my_role.position},captain pos={game.captain_pos}')
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()

        target_role = _get_role_by_pos(game, target)
        if not target_role.alive:
            current_app.logger.info(f'target not alive, target={target}')
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        game.captain_pos = target
        publish_history(game.gid, f'{my_role.position}号玩家将警徽移交给了{target}号玩家')
        return GameEnum.OK.digest()


def elect()->dict:
    choice = request.args.get('choice')
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
    with Game.query.with_for_update().get(current_user.gid) as game:
        now = StepProcessor.current_step(game)
        if choice in ['yes', 'no'] and now is not GameEnum.TURN_STEP_ELECT:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if choice == 'quit' and now is not GameEnum.TURN_STEP_ELECT_TALK:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if choice in ['yes', 'no'] and (GameEnum.TAG_ELECT in my_role.tags or GameEnum.TAG_NOT_ELECT in my_role.tags):
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if choice == 'quit' and (GameEnum.TAG_ELECT not in my_role.tags or GameEnum.TAG_GIVE_UP_ELECT in my_role.tags):
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()

        if choice == 'yes':
            my_role.tags.append(GameEnum.TAG_ELECT)
        elif choice == 'no':
            my_role.tags.append(GameEnum.TAG_NOT_ELECT)
        elif choice == 'quit':
            publish_history(game.gid, f'{my_role.position}号玩家退水')
            my_role.tags.remove(GameEnum.TAG_ELECT)
            my_role.tags.append(GameEnum.TAG_GIVE_UP_ELECT)
            votee = game.history['voter_votee'][1]
            votee.remove(my_role.position)
            if len(votee) == 1:
                while game.now_index + 1 < len(game.steps) and game.steps[game.now_index + 1] in {GameEnum.TURN_STEP_ELECT_TALK, GameEnum.TURN_STEP_ELECT_VOTE}:
                    game.steps.pop(game.now_index + 1)
                captain_pos = votee[0]
                game.captain_pos = captain_pos
                publish_history(game.gid, f'仅剩一位警上玩家，{captain_pos}号玩家自动当选警长')
                return StepProcessor.move_on(game)
        else:
            raise ValueError(f'Unknown choice: {choice}')
        return GameEnum.OK.digest()


def wolf_kill()->dict:
    target = int(request.args.get('target'))
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
    with Game.query.with_for_update().get(current_user.gid) as game:
        now = StepProcessor.current_step(game)
        history = game.history
        if now != GameEnum.TAG_ATTACKABLE_WOLF or GameEnum.TAG_ATTACKABLE_WOLF not in my_role.tags:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if game.wolf_mode is GameEnum.WOLF_MODE_FIRST:
            history['wolf_kill_decision'] = target
        else:
            history['wolf_kill'][my_role.position] = target
            history.changed()
            all_players = Role.query.filter(Role.gid == game.gid, Role.alive == int(True)).limit(len(game.players)).all()
            attackable_cnt = 0
            for p in all_players:
                if GameEnum.TAG_ATTACKABLE_WOLF in p.tags:
                    attackable_cnt += 1
            if attackable_cnt == len(history['wolf_kill']):
                decision = set(history['wolf_kill'].values())
                if len(decision) == 1:
                    history['wolf_kill_decision'] = decision.pop()
                else:
                    history['wolf_kill_decision'] = GameEnum.TARGET_NO_ONE.value
        StepProcessor.move_on(game)
        if target > 0:
            return GameEnum.OK.digest(result=f'你选择了击杀{target}号玩家')
        else:
            return GameEnum.OK.digest(result=f'你选择空刀')


def discover()->dict:
    target = int(request.args.get('target'))
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
    with Game.query.with_for_update().get(current_user.gid) as game:
        history = game.history
        now = StepProcessor.current_step(game)
        if now is not GameEnum.ROLE_TYPE_SEER or my_role.role_type is not GameEnum.ROLE_TYPE_SEER:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if history['discover'] != GameEnum.TARGET_NOT_ACTED.value:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        target_role = _get_role_by_pos(game, target)
        if not target_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        history['discover'] = target
        group_result = '<span style="color:red">狼人</span>' if target_role.group_type is GameEnum.GROUP_TYPE_WOLVES else '<span style="color:green">好人</span>'
        StepProcessor.move_on(game)
        return GameEnum.OK.digest(result=f'你查验了{target}号玩家为：{group_result}')


def witch()->dict:
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
    with Game.query.with_for_update().get(current_user.gid) as game:
        history = game.history
        now = StepProcessor.current_step(game)
        if now is not GameEnum.ROLE_TYPE_WITCH or my_role.role_type is not GameEnum.ROLE_TYPE_WITCH:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if not my_role.args['elixir']:
            return GameEnum.OK.digest(result=GameEnum.TARGET_NOT_ACTED.value)
        else:
            return GameEnum.OK.digest(result=history['wolf_kill_decision'])


def elixir()->dict:
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
    with Game.query.with_for_update().get(current_user.gid) as game:
        history = game.history
        now = StepProcessor.current_step(game)
        if now is not GameEnum.ROLE_TYPE_WITCH or my_role.role_type is not GameEnum.ROLE_TYPE_WITCH:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if not my_role.args['elixir']:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if history['elixir'] or history['toxic'] != GameEnum.TARGET_NOT_ACTED.value:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if history['wolf_kill_decision'] == GameEnum.TARGET_NO_ONE.value:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        history['elixir'] = True
        my_role.args['elixir'] = False
        return GameEnum.OK.digest(result=f'你使用了解药')


def toxic()->dict:
    target = int(request.args.get('target'))
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
    with Game.query.with_for_update().get(current_user.gid) as game:
        history = game.history
        now = StepProcessor.current_step(game)
        if now is not GameEnum.ROLE_TYPE_WITCH or my_role.role_type is not GameEnum.ROLE_TYPE_WITCH:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if not my_role.args['toxic']:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if history['elixir'] or history['toxic'] != GameEnum.TARGET_NOT_ACTED.value:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        target_role = _get_role_by_pos(game, target)
        if not target_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        history['toxic'] = target
        my_role.args['toxic'] = False
        if target > 0:
            return GameEnum.OK.digest(result=f'你毒杀了{target}号玩家')
        else:
            return GameEnum.OK.digest()


def guard()->dict:
    target = int(request.args.get('target'))
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
    with Game.query.with_for_update().get(current_user.gid) as game:
        history = game.history
        now = StepProcessor.current_step(game)
        if now is not GameEnum.ROLE_TYPE_SAVIOR or my_role.role_type is not GameEnum.ROLE_TYPE_SAVIOR:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if my_role.args['guard'] != GameEnum.TARGET_NO_ONE.value and my_role.args['guard'] == target:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if history['guard'] != GameEnum.TARGET_NOT_ACTED.value:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        target_role = _get_role_by_pos(game, target)
        if not target_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        history['guard'] = target
        my_role.args['guard'] = target
        if target > 0:
            return GameEnum.OK.digest(result=f'你守护了{target}号玩家')
        else:
            return GameEnum.OK.digest(result=f'你选择空守')


def shoot()->dict:
    target = int(request.args.get('target'))
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
    with Game.query.with_for_update().get(current_user.gid) as game:
        history = game.history
        now = StepProcessor.current_step(game)
        if now is not GameEnum.TURN_STEP_LAST_WORDS:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        if not my_role.args['shootable'] or str(my_role.position) not in game.history['dying']:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        publish_history(game.gid, f'{my_role.position}号玩家发动技能“枪击”，带走了{target}号玩家')
        StepProcessor.kill(game, target, GameEnum.SKILL_SHOOT)
        return GameEnum.OK.digest()


def suicide():
    my_role = Role.query.get(current_user.uid)
    if not my_role.alive:
        return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()

    with Game.query.with_for_update().get(current_user.gid) as game:
        if game.status is not GameEnum.GAME_STATUS_DAY:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        game.history = game.history[:game.now_index + 1]
        publish_history(game.gid, f'{my_role.position}号玩家自爆了')
        StepProcessor.kill(game, my_role.position, GameEnum.SKILL_SUICIDE)
        return GameEnum.OK.digest()


def _get_wolf_mode_by_cards(cards):
    # WOLF_MODE_FIRST if there is no thrid party, else WOLF_MODE_ALL
    if GameEnum.ROLE_TYPE_CUPID in cards:
        return GameEnum.WOLF_MODE_ALL
    else:
        return GameEnum.WOLF_MODE_FIRST


def _get_role_by_pos(game, pos):
    uid = game.players[pos - 1]
    return Role.query.get(uid)
