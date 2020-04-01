from datetime import datetime, timedelta
import json
import random
import collections
from flask import request, current_app
from flask_login import current_user
from sqlalchemy import func
from werewolf.utils.game_exceptions import GameFinished
from werewolf.database import db, User, Game, Role
from werewolf.utils.enums import GameEnum
from werewolf.utils.json_utils import json_hook, ExtendedJSONEncoder
from werewolf.utils.publisher import publish_info, publish_history, publish_music
from werewolf.utils.game_scheduler import scheduler


class GameEngine(object):
    def __init__(self):
        raise TypeError('Cannot instantiate this class')

    @staticmethod
    def perform(cmd):
        try:
            f = getattr(GameEngine, f'_api_{cmd}')
            return f()
        except GameFinished:
            return GameEnum.OK.digest()

    @staticmethod
    def _api_setup() -> dict:
        victory_mode = GameEnum['VICTORY_MODE_{}'.format(request.form['victoryMode'].upper())]
        captain_mode = GameEnum['CAPTAIN_MODE_{}'.format(request.form['captainMode'].upper())]
        witch_mode = GameEnum['WITCH_MODE_{}'.format(request.form['witchMode'].upper())]
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
                        wolf_mode=GameEngine._get_wolf_mode_by_cards(cards),
                        cards=cards,
                        )
        GameEngine._init_game(new_game)
        db.session.add(new_game)
        db.session.commit()

        return GameEnum.OK.digest(gid=new_game.gid)

    @staticmethod
    def _api_join() -> dict:
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

    @staticmethod
    def _api_quit() -> dict:
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

    @staticmethod
    def _api_deal() -> dict:
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

    @staticmethod
    def _api_get_game_info() -> dict:
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

    @staticmethod
    def _api_sit()->dict:
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

    @staticmethod
    def _api_next_step()->dict:
        with Game.query.with_for_update().get(current_user.gid) as game:
            if game.status not in [GameEnum.GAME_STATUS_READY, GameEnum.GAME_STATUS_DAY]:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            return GameEngine._move_on(game)

    @staticmethod
    def _api_vote()->dict:
        target = int(request.args.get('target'))
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        with Game.query.with_for_update().get(current_user.gid) as game:
            if not my_role.voteable or my_role.position not in game.history['voter_votee'][0]:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if target != GameEnum.TARGET_NO_ONE.value and target not in game.history['voter_votee'][1]:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if target > 0:
                target_role = GameEngine._get_role_by_pos(game, target)
                if not target_role.alive:
                    return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()

            now = GameEngine._current_step(game)
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

    @staticmethod
    def _api_handover()->dict:
        target = int(request.args.get('target'))
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            current_app.logger.info('my_role is not alive')
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        with Game.query.with_for_update().get(current_user.gid) as game:
            now = GameEngine._current_step(game)
            if now is not GameEnum.TURN_STEP_LAST_WORDS:
                current_app.logger.info(f'wrong now step:{now.label}')
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if str(my_role.position) not in game.history['dying']:
                current_app.logger.info(f'not in dying: my position={my_role.position},dying={game.history["dying"]}')
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if game.captain_pos != my_role.position:
                current_app.logger.info(f'I am not captain, my position={my_role.position},captain pos={game.captain_pos}')
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if target > 0:
                target_role = GameEngine._get_role_by_pos(game, target)
                if not target_role.alive:
                    current_app.logger.info(f'target not alive, target={target}')
                    return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            game.captain_pos = target
            publish_history(game.gid, f'{my_role.position}号玩家将警徽移交给了{target}号玩家')
            return GameEnum.OK.digest()

    @staticmethod
    def _api_elect()->dict:
        choice = request.args.get('choice')
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        with Game.query.with_for_update().get(current_user.gid) as game:
            now = GameEngine._current_step(game)
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
                    return GameEngine._move_on(game)
            else:
                raise ValueError(f'Unknown choice: {choice}')
            return GameEnum.OK.digest()

    @staticmethod
    def _api_wolf_kill()->dict:
        target = int(request.args.get('target'))
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        with Game.query.with_for_update().get(current_user.gid) as game:
            now = GameEngine._current_step(game)
            history = game.history
            if now != GameEnum.TAG_ATTACKABLE_WOLF or GameEnum.TAG_ATTACKABLE_WOLF not in my_role.tags:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if target > 0:
                target_role = GameEngine._get_role_by_pos(game, target)
                if not target_role.alive:
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
            GameEngine._move_on(game)
            if target > 0:
                return GameEnum.OK.digest(result=f'你选择了击杀{target}号玩家')
            else:
                return GameEnum.OK.digest(result=f'你选择空刀')

    @staticmethod
    def _api_discover()->dict:
        target = int(request.args.get('target'))
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        with Game.query.with_for_update().get(current_user.gid) as game:
            history = game.history
            now = GameEngine._current_step(game)
            if now is not GameEnum.ROLE_TYPE_SEER or my_role.role_type is not GameEnum.ROLE_TYPE_SEER:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if history['discover'] != GameEnum.TARGET_NOT_ACTED.value:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if target > 0:
                target_role = GameEngine._get_role_by_pos(game, target)
                if not target_role.alive:
                    return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            history['discover'] = target
            group_result = '<span style="color:red">狼人</span>' if target_role.group_type is GameEnum.GROUP_TYPE_WOLVES else '<span style="color:green">好人</span>'
            GameEngine._move_on(game)
            return GameEnum.OK.digest(result=f'你查验了{target}号玩家为：{group_result}')

    @staticmethod
    def _api_witch()->dict:
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        with Game.query.with_for_update().get(current_user.gid) as game:
            history = game.history
            now = GameEngine._current_step(game)
            if now is not GameEnum.ROLE_TYPE_WITCH or my_role.role_type is not GameEnum.ROLE_TYPE_WITCH:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if not my_role.args['elixir']:
                return GameEnum.OK.digest(result=GameEnum.TARGET_NOT_ACTED.value)
            else:
                return GameEnum.OK.digest(result=history['wolf_kill_decision'])

    @staticmethod
    def _api_elixir()->dict:
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        with Game.query.with_for_update().get(current_user.gid) as game:
            history = game.history
            now = GameEngine._current_step(game)
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

    @staticmethod
    def _api_toxic()->dict:
        target = int(request.args.get('target'))
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        with Game.query.with_for_update().get(current_user.gid) as game:
            history = game.history
            now = GameEngine._current_step(game)
            if now is not GameEnum.ROLE_TYPE_WITCH or my_role.role_type is not GameEnum.ROLE_TYPE_WITCH:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if not my_role.args['toxic']:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if history['elixir'] or history['toxic'] != GameEnum.TARGET_NOT_ACTED.value:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if target > 0:
                target_role = GameEngine._get_role_by_pos(game, target)
                if not target_role.alive:
                    return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            history['toxic'] = target
            if target > 0:
                my_role.args['toxic'] = False
            GameEngine._move_on(game)
            if target > 0:
                return GameEnum.OK.digest(result=f'你毒杀了{target}号玩家')
            else:
                return GameEnum.OK.digest()

    @staticmethod
    def _api_guard()->dict:
        target = int(request.args.get('target'))
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        with Game.query.with_for_update().get(current_user.gid) as game:
            history = game.history
            now = GameEngine._current_step(game)
            if now is not GameEnum.ROLE_TYPE_SAVIOR or my_role.role_type is not GameEnum.ROLE_TYPE_SAVIOR:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if my_role.args['guard'] != GameEnum.TARGET_NO_ONE.value and my_role.args['guard'] == target:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if history['guard'] != GameEnum.TARGET_NOT_ACTED.value:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if target > 0:
                target_role = GameEngine._get_role_by_pos(game, target)
                if not target_role.alive:
                    return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            history['guard'] = target
            my_role.args['guard'] = target
            GameEngine._move_on(game)
            if target > 0:
                return GameEnum.OK.digest(result=f'你守护了{target}号玩家')
            else:
                return GameEnum.OK.digest(result=f'你选择空守')

    @staticmethod
    def _api_shoot()->dict:
        target = int(request.args.get('target'))
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
        with Game.query.with_for_update().get(current_user.gid) as game:
            history = game.history
            now = GameEngine._current_step(game)
            if now is not GameEnum.TURN_STEP_LAST_WORDS:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if not my_role.args['shootable'] or str(my_role.position) not in game.history['dying']:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            if target > 0:
                target_role = GameEngine._get_role_by_pos(game, target)
                if not target_role.alive:
                    return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            publish_history(game.gid, f'{my_role.position}号玩家发动技能“枪击”，带走了{target}号玩家')
            GameEngine._kill(game, target, GameEnum.SKILL_SHOOT)
            return GameEnum.OK.digest()

    @staticmethod
    def _api_suicide():
        my_role = Role.query.get(current_user.uid)
        if not my_role.alive:
            return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()

        with Game.query.with_for_update().get(current_user.gid) as game:
            if game.status is not GameEnum.GAME_STATUS_DAY:
                return GameEnum.GAME_MESSAGE_CANNOT_ACT.digest()
            game.steps = []
            publish_history(game.gid, f'{my_role.position}号玩家自爆了')
            GameEngine._kill(game, my_role.position, GameEnum.SKILL_SUICIDE)
            return GameEngine._move_on(game)

    #################################
    #        NON-API METHODS        #
    #################################

    @staticmethod
    def _get_wolf_mode_by_cards(cards):
        # WOLF_MODE_FIRST if there is no thrid party, else WOLF_MODE_ALL
        if GameEnum.ROLE_TYPE_CUPID in cards:
            return GameEnum.WOLF_MODE_ALL
        else:
            return GameEnum.WOLF_MODE_FIRST

    @staticmethod
    def _get_role_by_pos(game, pos):
        if pos < 0:
            return None
        uid = game.players[pos - 1]
        return Role.query.get(uid)

    @staticmethod
    def _move_on(game: Game)->dict:
        step_flag = GameEnum.STEP_FLAG_AUTO_MOVE_ON
        while step_flag is GameEnum.STEP_FLAG_AUTO_MOVE_ON:
            leave_result = GameEngine._leave_step(game)
            if leave_result['code'] != GameEnum.OK.value:
                return leave_result

            game.step_cnt += 1
            game.now_index += 1
            if game.now_index >= len(game.steps):
                game.now_index = 0
                game.days += 1
                GameEngine._init_steps(game)

            step_flag = GameEngine._enter_step(game)
        instruction_string = GameEngine.get_instruction_string(game)
        if instruction_string:
            publish_info(game.gid, json.dumps({'next_step': instruction_string}))
        return GameEnum.OK.digest()

    @staticmethod
    def _leave_step(game: Game)->dict:
        now = GameEngine._current_step(game)
        if now is None:
            return GameEnum.OK.digest()
        if now is GameEnum.TURN_STEP_ELECT:
            roles = Role.query.filter(Role.gid == game.gid).limit(len(game.players)).all()
            for r in roles:
                if GameEnum.TAG_ELECT not in r.tags and GameEnum.TAG_NOT_ELECT not in r.tags:
                    r.tags.append(GameEnum.TAG_NOT_ELECT)

            voters = []
            votees = []
            for r in roles:
                if not r.alive:
                    continue
                if GameEnum.TAG_ELECT in r.tags:
                    votees.append(r.position)
                else:
                    voters.append(r.position)
            voters.sort()
            votees.sort()

            if not voters or not votees:
                # no captain
                while game.now_index + 1 < len(game.steps) and game.steps[game.now_index + 1] in {GameEnum.TURN_STEP_ELECT_TALK, GameEnum.TURN_STEP_ELECT_VOTE}:
                    game.steps.pop(game.now_index + 1)
                if not voters:
                    publish_history(game.gid, '所有人都竞选警长，本局游戏无警长')
                else:
                    publish_history(game.gid, '没有人竞选警长，本局游戏无警长')
            elif len(votees) == 1:
                # auto win captain
                while game.now_index + 1 < len(game.steps) and game.steps[game.now_index + 1] in {GameEnum.TURN_STEP_ELECT_TALK, GameEnum.TURN_STEP_ELECT_VOTE}:
                    game.steps.pop(game.now_index + 1)
                captain_pos = votees[0]
                game.captain_pos = captain_pos
                publish_history(game.gid, f'只有{captain_pos}号玩家竞选警长，自动当选')
            else:
                publish_history(game.gid, f"竞选警长的玩家为：{','.join(map(str,votees))}\n未竞选警长的玩家为：{','.join(map(str,voters))}")
                game.history['voter_votee'] = [voters, votees]
            return GameEnum.OK.digest()
        elif now in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_ELECT_VOTE, GameEnum.TURN_STEP_PK_VOTE, GameEnum.TURN_STEP_ELECT_PK_VOTE]:
            msg = ""
            announce_result = collections.defaultdict(list)
            ticket_cnt = collections.defaultdict(int)
            forfeit = []
            most_voted = []
            max_ticket = 0
            for voter_pos, votee_pos in game.history['vote_result'].items():
                voter_pos = int(voter_pos)
                votee_pos = int(votee_pos)
                if votee_pos in [GameEnum.TARGET_NOT_ACTED.value, GameEnum.TARGET_NO_ONE.value]:
                    forfeit.append(voter_pos)
                    continue
                announce_result[votee_pos].append(voter_pos)
                ticket_cnt[votee_pos] += 1
                if voter_pos == game.captain_pos:
                    ticket_cnt[votee_pos] += 0.5
            for voter in game.history['voter_votee'][0]:
                if str(voter) not in game.history['vote_result']:
                    forfeit.append(voter)
            if forfeit and now in [GameEnum.TURN_STEP_PK_VOTE, GameEnum.TURN_STEP_ELECT_PK_VOTE]:
                return GameEnum.GAME_MESSAGE_NOT_VOTED_YET.digest(*forfeit)
            for votee, voters in sorted(announce_result.items()):
                msg += '{} <= {}\n'.format(votee, ','.join(map(str, voters)))
            if forfeit:
                msg += '弃票：{}\n'.format(','.join(map(str, forfeit)))

            if not ticket_cnt:
                most_voted = game.history['voter_votee'][1]
            else:
                ticket_cnt = sorted(ticket_cnt.items(), key=lambda x: x[1], reverse=True)
                most_voted.append(ticket_cnt[0][0])
                max_ticket = ticket_cnt[0][1]
                for votee, ticket in ticket_cnt[1:]:
                    if ticket == max_ticket:
                        most_voted.append(votee)
                    else:
                        break
            most_voted.sort()

            if len(most_voted) == 1:
                if now in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_PK_VOTE]:
                    msg += f'{most_voted[0]}号玩家以{max_ticket}票被公投出局'
                    publish_history(game.gid, msg)
                    GameEngine._kill(game, most_voted[0], GameEnum.SKILL_VOTE)
                else:
                    game.captain_pos = most_voted[0]
                    msg += f'{most_voted[0]}号玩家以{max_ticket}票当选警长'
                    publish_history(game.gid, msg)
                return GameEnum.OK.digest()
            else:
                # 平票
                # todo 无人投票
                if now in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_ELECT_VOTE]:
                    if now is GameEnum.TURN_STEP_VOTE:
                        game.steps.insert(game.now_index + 1, GameEnum.TURN_STEP_PK_TALK)
                        game.steps.insert(game.now_index + 2, GameEnum.TURN_STEP_PK_VOTE)
                    else:
                        game.steps.insert(game.now_index + 1, GameEnum.TURN_STEP_ELECT_PK_TALK)
                        game.steps.insert(game.now_index + 2, GameEnum.TURN_STEP_ELECT_PK_VOTE)
                    votees = most_voted
                    voters = []
                    roles = Role.query.filter(Role.gid == game.gid).limit(len(game.players)).all()
                    for r in roles:
                        if r.alive and r.voteable and r.position not in votees:
                            voters.append(r.position)
                    game.history['voter_votee'] = [voters, votees]
                    msg += '以下玩家以{}票平票进入PK：{}'.format(max_ticket, ','.join(map(str, votees)))
                    publish_history(game.gid, msg)
                    return GameEnum.OK.digest()
                else:
                    msg += '以下玩家以{}票再次平票：{}\n'.format(max_ticket, ','.join(map(str, most_voted)))
                    if now is GameEnum.TURN_STEP_PK_VOTE:
                        msg += '今天是平安日，无人被公投出局'
                    else:
                        msg += '警徽流失，本局游戏无警长'
                    publish_history(game.gid, msg)
                    return GameEnum.OK.digest()
        elif now is GameEnum.TAG_ATTACKABLE_WOLF:
            publish_music(game.gid, 'wolf_end_voice', None, False)
            return GameEnum.OK.digest()
        elif now is GameEnum.ROLE_TYPE_SEER:
            publish_music(game.gid, 'seer_end_voice', None, False)
            return GameEnum.OK.digest()
        elif now is GameEnum.ROLE_TYPE_WITCH:
            publish_music(game.gid, 'witch_end_voice', None, False)
            return GameEnum.OK.digest()
        elif now is GameEnum.ROLE_TYPE_SAVIOR:
            publish_music(game.gid, 'savior_end_voice', None, False)
            return GameEnum.OK.digest()
        else:
            return GameEnum.OK.digest()

    @staticmethod
    def _enter_step(game: Game)->GameEnum:
        now = GameEngine._current_step(game)
        if now is GameEnum.TURN_STEP_TURN_NIGHT:
            game.status = GameEnum.GAME_STATUS_NIGHT
            for d in game.history['dying']:
                role = Role.query.filter(Role.gid == game.gid, Role.position == d).limit(1).first()
                role.alive = False
            GameEngine._reset_history(game)
            publish_music(game.gid, 'night_start_voice', 'night_bgm', True)
            publish_info(game.gid, json.dumps({'days': game.days, 'game_status': game.status.label}))
            publish_history(game.gid,
                            (
                                '***************************\n'
                                '<pre>         第{}天           </pre>\n'
                                '***************************'
                            ).format(game.days), show=False)
            return GameEnum.STEP_FLAG_AUTO_MOVE_ON
        elif now is GameEnum.TAG_ATTACKABLE_WOLF:
            publish_music(game.gid, 'wolf_start_voice', 'wolf_bgm', True)
            all_players = Role.query.filter(Role.gid == game.gid, Role.alive == int(True)).limit(len(game.players)).all()
            for p in all_players:
                if GameEnum.TAG_ATTACKABLE_WOLF in p.tags:
                    break
            else:
                scheduler.add_job(id=f'{game.gid}_WOLF_KILL_{game.step_cnt}', func=GameEngine._timeout_move_on,
                                  args=(game.gid, game.step_cnt),
                                  next_run_time=datetime.now() + timedelta(seconds=random.randint(GameEnum.GAME_TIMEOUT_RANDOM_FROM.label, GameEnum.GAME_TIMEOUT_RANDOM_TO.label)))
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now in [GameEnum.TURN_STEP_TALK, GameEnum.TURN_STEP_ELECT_TALK]:
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now is GameEnum.TURN_STEP_ELECT:
            publish_music(game.gid, 'elect', None, False)
            publish_history(game.gid, '###上警阶段###', False)
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now is GameEnum.TURN_STEP_VOTE:
            game.history['vote_result'] = {}
            voters = []
            votees = []
            roles = Role.query.filter(Role.gid == game.gid).limit(len(game.players)).all()
            for r in roles:
                if not r.alive:
                    continue
                votees.append(r.position)
                if r.voteable:
                    voters.append(r.position)
            game.history['voter_votee'] = [voters, votees]
            publish_history(game.gid, '###投票阶段###', False)
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now is GameEnum.TURN_STEP_ELECT_VOTE:
            game.history['vote_result'] = {}
            publish_history(game.gid, '###警长投票阶段###', False)
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now is GameEnum.TURN_STEP_PK_VOTE:
            game.history['vote_result'] = {}
            publish_history(game.gid, '###PK投票阶段###', False)
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now is GameEnum.TURN_STEP_ELECT_PK_VOTE:
            game.history['vote_result'] = {}
            publish_history(game.gid, '###警长PK投票阶段###', False)
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now is GameEnum.TURN_STEP_ANNOUNCE:
            if game.history['dying']:
                publish_history(game.gid, '昨晚，以下位置的玩家倒下了，不分先后：{}'.format(
                    ','.join([str(d) for d in sorted(game.history['dying'])])
                ))
            else:
                publish_history(game.gid, "昨晚是平安夜")
            return GameEnum.STEP_FLAG_AUTO_MOVE_ON
        elif now is GameEnum.TURN_STEP_TURN_DAY:
            game.status = GameEnum.GAME_STATUS_DAY
            publish_music(game.gid, 'day_start_voice', 'day_bgm', False)
            GameEngine._calculate_die_in_night(game)
            publish_info(game.gid, json.dumps({'days': game.days, 'game_status': game.status.label}))
            return GameEnum.STEP_FLAG_AUTO_MOVE_ON
        elif now is GameEnum.ROLE_TYPE_SEER:
            publish_music(game.gid, 'seer_start_voice', 'seer_bgm', True)
            seer_cnt = db.session.query(db.func.count(Role.uid)).filter(Role.gid == game.gid, Role.alive == int(True),
                                                                        Role.role_type == GameEnum.ROLE_TYPE_SEER).scalar()
            if seer_cnt == 0:
                scheduler.add_job(id=f'{game.gid}_SEER_{game.step_cnt}', func=GameEngine._timeout_move_on,
                                  args=(game.gid, game.step_cnt),
                                  next_run_time=datetime.now() + timedelta(seconds=random.randint(GameEnum.GAME_TIMEOUT_RANDOM_FROM.label, GameEnum.GAME_TIMEOUT_RANDOM_TO.label)))
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now is GameEnum.ROLE_TYPE_WITCH:
            publish_music(game.gid, 'witch_start_voice', 'witch_bgm', True)
            witch_cnt = db.session.query(db.func.count(Role.uid)).filter(Role.gid == game.gid, Role.alive == int(True),
                                                                         Role.role_type == GameEnum.ROLE_TYPE_WITCH).scalar()
            if witch_cnt == 0:
                scheduler.add_job(id=f'{game.gid}_WITCH_{game.step_cnt}', func=GameEngine._timeout_move_on,
                                  args=(game.gid, game.step_cnt),
                                  next_run_time=datetime.now() + timedelta(seconds=random.randint(GameEnum.GAME_TIMEOUT_RANDOM_FROM.label, GameEnum.GAME_TIMEOUT_RANDOM_TO.label)))
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now is GameEnum.ROLE_TYPE_SAVIOR:
            publish_music(game.gid, 'savior_start_voice', 'savior_bgm', True)
            savior_cnt = db.session.query(db.func.count(Role.uid)).filter(Role.gid == game.gid, Role.alive == int(True),
                                                                          Role.role_type == GameEnum.ROLE_TYPE_SAVIOR).scalar()
            if savior_cnt == 0:
                scheduler.add_job(id=f'{game.gid}_SAVIOR', func=GameEngine._timeout_move_on,
                                  args=(game.gid, game.step_cnt),
                                  next_run_time=datetime.now() + timedelta(seconds=random.randint(GameEnum.GAME_TIMEOUT_RANDOM_FROM.label, GameEnum.GAME_TIMEOUT_RANDOM_TO.label)))
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION

    @staticmethod
    def get_instruction_string(game: Game)->str:
        now = GameEngine._current_step(game)
        if now in [GameEnum.TURN_STEP_TALK, GameEnum.TURN_STEP_PK_TALK, GameEnum.TURN_STEP_ELECT_TALK, GameEnum.TURN_STEP_ELECT_PK_TALK, GameEnum.TURN_STEP_LAST_WORDS]:
            return '结束发言'

        if now in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_PK_VOTE, GameEnum.TURN_STEP_ELECT_VOTE, GameEnum.TURN_STEP_ELECT_PK_VOTE]:
            return '结束投票'

        if now is GameEnum.TURN_STEP_ELECT:
            return '结束上警'

        next_index = game.now_index + 1
        if next_index >= len(game.steps):
            step = GameEnum.TURN_STEP_TURN_NIGHT
        else:
            step = game.steps[next_index]

        if step is GameEnum.TURN_STEP_TURN_NIGHT:
            return '入夜'

        return ''

    @staticmethod
    def _current_step(game: Game)->GameEnum:
        if game.now_index < 0 or game.now_index >= len(game.steps):
            return None
        else:
            return game.steps[game.now_index]

    @staticmethod
    def _init_steps(game: Game):
        game.steps = [GameEnum.TURN_STEP_TURN_NIGHT]
        if game.days == 1 and GameEnum.ROLE_TYPE_THIEF in game.cards:
            pass  # todo
        if game.days == 1 and GameEnum.ROLE_TYPE_CUPID in game.cards:
            pass  # todo
        # TODO: 恋人互相确认身份
        game.steps.append(GameEnum.TAG_ATTACKABLE_WOLF)
        if GameEnum.ROLE_TYPE_SEER in game.cards:
            game.steps.append(GameEnum.ROLE_TYPE_SEER)
        if GameEnum.ROLE_TYPE_WITCH in game.cards:
            game.steps.append(GameEnum.ROLE_TYPE_WITCH)
        if GameEnum.ROLE_TYPE_SAVIOR in game.cards:
            game.steps.append(GameEnum.ROLE_TYPE_SAVIOR)
        game.steps.append(GameEnum.TURN_STEP_TURN_DAY)
        if game.days == 1 and game.captain_mode is GameEnum.CAPTAIN_MODE_WITH_CAPTAIN:
            game.steps.append(GameEnum.TURN_STEP_ELECT)
            game.steps.append(GameEnum.TURN_STEP_ELECT_TALK)
            game.steps.append(GameEnum.TURN_STEP_ELECT_VOTE)
        game.steps.append(GameEnum.TURN_STEP_ANNOUNCE)
        game.steps.append(GameEnum.TURN_STEP_TALK)
        game.steps.append(GameEnum.TURN_STEP_VOTE)
        game.steps.append(GameEnum.TURN_STEP_LAST_WORDS)

        return

    @staticmethod
    def _reset_history(game):
        """
            pos: -1=no one, -2=not acted
            {
                'wolf_kill':{wolf_pos:target_pos,...},
                'wolf_kill_decision':pos,
                'elixir':True / False,
                'guard':pos,
                'toxic':pos,
                'discover':pos,
                'voter_votee':[[voter_pos,...],[votee_pos,...]],
                'vote_result': {voter_pos:votee_pos,...},
                'dying':{pos:True},
            }
        """
        game.history = {
            'wolf_kill': {},
            'wolf_kill_decision': GameEnum.TARGET_NOT_ACTED.value,
            'elixir': False,
            'guard': GameEnum.TARGET_NOT_ACTED.value,
            'toxic': GameEnum.TARGET_NOT_ACTED.value,
            'discover': GameEnum.TARGET_NOT_ACTED.value,
            'voter_votee': [[], []],
            'vote_result': {},
            'dying': {},
        }

    @staticmethod
    def _kill(game: Game, pos: int, how: GameEnum):
        current_app.logger.info(f'kill pos={pos},by {how.label}')
        if pos < 1 or pos > game.get_seats_cnt():
            return
        role = Role.query.filter(Role.gid == game.gid, Role.position == pos).limit(1).first()

        # todo 长老?

        if role is GameEnum.ROLE_TYPE_IDIOT and how is GameEnum.SKILL_VOTE and not role.args['exposed']:
            role.args['exposed'] = True
            role.voteable = False
            return

        game.history['dying'][pos] = True
        game.history.changed()

        if how is GameEnum.SKILL_TOXIC and role is GameEnum.ROLE_TYPE_HUNTER:
            role.args['shootable'] = False

        # todo: other link die
        # if game.status is GameEnum.GAME_STATUS_DAY:
        GameEngine._check_win(game)

    @staticmethod
    def _calculate_die_in_night(game):
        wolf_kill_pos = game.history['wolf_kill_decision']
        elixir = game.history['elixir']
        guard = game.history['guard']

        current_app.logger.info(f'wolf_kill_pos={wolf_kill_pos},elixir={elixir},guard={guard}')
        if wolf_kill_pos > 0:
            killed = True
            if elixir:
                killed = not killed
            if guard == wolf_kill_pos:
                killed = not killed

            if killed:
                GameEngine._kill(game, wolf_kill_pos, GameEnum.SKILL_WOLF_KILL)
        if game.history['toxic'] > 0:
            GameEngine._kill(game, game.history['toxic'], GameEnum.SKILL_TOXIC)
        # todo: other death way in night?
        return

    @staticmethod
    def _check_win(game):
        # groups = Role.query.with_entities(Role.group_type, func.count(Role.group_type)).filter(Role.gid == game.gid, Role.alive == int(True)).group_by(Role.group_type).all()
        # groups = {g: cnt for g, cnt in groups}

        players = Role.query.with_entities(Role.position, Role.group_type).filter(Role.gid == game.gid, Role.alive == int(True)).all()
        groups = collections.defaultdict(int)
        for p, g in players:
            if p not in game.history['dying']:
                groups[g] += 1

        if GameEnum.GROUP_TYPE_WOLVES not in groups:
            publish_history(game.gid, '游戏结束，好人阵营胜利')
            # game.status = GameEnum.GAME_STATUS_FINISHED
            original_players = game.players
            GameEngine._init_game(game)
            game.players = original_players
            all_players = Role.query.filter(Role.gid == game.gid).all()
            for p in all_players:
                p.reset()
            raise GameFinished()

        if game.victory_mode is GameEnum.VICTORY_MODE_KILL_GROUP and (GameEnum.GROUP_TYPE_GODS not in groups or GameEnum.GROUP_TYPE_VILLAGERS not in groups):
            publish_history(game.gid, '游戏结束，狼人阵营胜利')
            # game.status = GameEnum.GAME_STATUS_FINISHED
            original_players = game.players
            GameEngine._init_game(game)
            game.players = original_players
            all_players = Role.query.filter(Role.gid == game.gid).all()
            for p in all_players:
                p.reset()
            raise GameFinished()

        if GameEnum.GROUP_TYPE_GODS not in groups and GameEnum.GROUP_TYPE_VILLAGERS not in groups:
            publish_history(game.gid, '游戏结束，狼人阵营胜利')
            # game.status = GameEnum.GAME_STATUS_FINISHED
            original_players = game.players
            GameEngine._init_game(game)
            game.players = original_players
            all_players = Role.query.filter(Role.gid == game.gid).all()
            for p in all_players:
                p.reset()
            raise GameFinished()

        # todo third party

    @staticmethod
    def _init_game(game):
        game.status = GameEnum.GAME_STATUS_WAIT_TO_START
        game.end_time = datetime.utcnow() + timedelta(days=1)
        game.days = 0
        game.now_index = -1
        game.step_cnt = 0
        game.steps = []
        game.history = {}
        game.captain_pos = -1
        game.players = []
        GameEngine._reset_history(game)

    @staticmethod
    def _timeout_move_on(gid, step_cnt):
        with scheduler.app.test_request_context():
            with Game.query.with_for_update().get(gid) as game:
                if step_cnt != game.step_cnt:
                    return GameEngine._move_on(game)
