# from __future__ import annotations
# import typing
import collections
import json
from sqlalchemy import func
from flask import current_app
from datetime import datetime, timedelta
import random
from werewolf.utils.enums import GameEnum
from werewolf.database import db, Role, Game
from werewolf.utils.publisher import publish_history, publish_music, publish_info
from werewolf.utils.game_exceptions import GameFinished
from werewolf.utils.game_scheduler import scheduler

# if typing.TYPE_CHECKING:
#     from werewolf.database import Game


class StepProcessor(object):
    @staticmethod
    def move_on(game: Game)->dict:
        step_flag = GameEnum.STEP_FLAG_AUTO_MOVE_ON
        while step_flag is GameEnum.STEP_FLAG_AUTO_MOVE_ON:
            leave_result = StepProcessor._leave_step(game)
            if leave_result['code'] != GameEnum.OK.value:
                return leave_result

            game.step_cnt += 1
            game.now_index += 1
            if game.now_index >= len(game.steps):
                game.now_index = 0
                game.days += 1
                StepProcessor.init_steps(game)

            step_flag = StepProcessor._enter_step(game)
        instruction_string = StepProcessor.get_instruction_string(game)
        if instruction_string:
            publish_info(game.gid, json.dumps({'next_step': instruction_string}))
        return GameEnum.OK.digest()

    @staticmethod
    def _leave_step(game: Game)->dict:
        now = StepProcessor.current_step(game)
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
                if voter not in game.history['vote_result']:
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
                    StepProcessor.kill(game, most_voted[0], GameEnum.SKILL_VOTE)
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
        now = StepProcessor.current_step(game)
        if now is GameEnum.TURN_STEP_TURN_NIGHT:
            game.status = GameEnum.GAME_STATUS_NIGHT
            for d in game.history['dying']:
                role = Role.query.filter(Role.gid == game.gid, Role.position == d).limit(1).first()
                role.alive = False
            StepProcessor._reset_history(game)
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
                scheduler.add_job(id=f'{game.gid}_WOLF_KILL_{game.step_cnt}', func=timeout_move_on,
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
                publish_history(game.gid, GameEnum.GAME_MESSAGE_DIE_IN_NIGHT.digest(
                    ','.join([str(d) for d in sorted(game.history['dying'])])
                ))
            else:
                publish_history(game.gid, "昨晚是平安夜")
            return GameEnum.STEP_FLAG_AUTO_MOVE_ON
        elif now is GameEnum.TURN_STEP_TURN_DAY:
            game.status = GameEnum.GAME_STATUS_DAY
            publish_music(game.gid, 'day_start_voice', 'day_bgm', False)
            StepProcessor.calculate_die_in_night(game)
            publish_info(game.gid, json.dumps({'days': game.days, 'game_status': game.status.label}))
            return GameEnum.STEP_FLAG_AUTO_MOVE_ON
        elif now is GameEnum.ROLE_TYPE_SEER:
            publish_music(game.gid, 'seer_start_voice', 'seer_bgm', True)
            seer_cnt = db.session.query(db.func.count(Role.uid)).filter(Role.gid == game.gid, Role.alive == int(True), Role.role_type == GameEnum.ROLE_TYPE_SEER).scalar()
            if seer_cnt == 0:
                scheduler.add_job(id=f'{game.gid}_SEER_{game.step_cnt}', func=timeout_move_on,
                                  args=(game.gid, game.step_cnt),
                                  next_run_time=datetime.now() + timedelta(seconds=5))
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now is GameEnum.ROLE_TYPE_WITCH:
            publish_music(game.gid, 'witch_start_voice', 'witch_bgm', True)
            witch_cnt = db.session.query(db.func.count(Role.uid)).filter(Role.gid == game.gid, Role.alive == int(True), Role.role_type == GameEnum.ROLE_TYPE_WITCH).scalar()
            if witch_cnt == 0:
                scheduler.add_job(id=f'{game.gid}_WITCH_{game.step_cnt}', func=timeout_move_on,
                                  args=(game.gid, game.step_cnt),
                                  next_run_time=datetime.now() + timedelta(seconds=random.randint(GameEnum.GAME_TIMEOUT_RANDOM_FROM.label, GameEnum.GAME_TIMEOUT_RANDOM_TO.label)))
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION
        elif now is GameEnum.ROLE_TYPE_SAVIOR:
            publish_music(game.gid, 'savior_start_voice', 'savior_bgm', True)
            savior_cnt = db.session.query(db.func.count(Role.uid)).filter(Role.gid == game.gid, Role.alive == int(True), Role.role_type == GameEnum.ROLE_TYPE_SAVIOR).scalar()
            if savior_cnt == 0:
                scheduler.add_job(id=f'{game.gid}_SAVIOR', func=timeout_move_on,
                                  args=(game.gid, game.step_cnt),
                                  next_run_time=datetime.now() + timedelta(seconds=random.randint(GameEnum.GAME_TIMEOUT_RANDOM_FROM.label, GameEnum.GAME_TIMEOUT_RANDOM_TO.label)))
            return GameEnum.STEP_FLAG_WAIT_FOR_ACTION

    @staticmethod
    def get_instruction_string(game: Game)->str:
        now = StepProcessor.current_step(game)
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
    def current_step(game: Game)->GameEnum:
        if game.now_index < 0 or game.now_index >= len(game.steps):
            return None
        else:
            return game.steps[game.now_index]

    @staticmethod
    def init_steps(game: Game):
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
    def kill(game: Game, pos: int, how: GameEnum):
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
        StepProcessor.check_win(game)

    @staticmethod
    def calculate_die_in_night(game):
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
                StepProcessor.kill(game, wolf_kill_pos, GameEnum.SKILL_WOLF_KILL)
        if game.history['toxic'] > 0:
            StepProcessor.kill(game, game.history['toxic'], GameEnum.SKILL_TOXIC)
        # todo: other death way in night?
        return

    @staticmethod
    def check_win(game):
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
            StepProcessor.init_game(game)
            all_players = Role.query.filter(Role.gid == game.gid).all()
            for p in all_players:
                p.reset()
            raise GameFinished()

        if game.victory_mode is GameEnum.VICTORY_MODE_KILL_GROUP and (GameEnum.GROUP_TYPE_GODS not in groups or GameEnum.GROUP_TYPE_VILLAGERS not in groups):
            publish_history(game.gid, '游戏结束，狼人阵营胜利')
            # game.status = GameEnum.GAME_STATUS_FINISHED
            StepProcessor.init_game(game)
            all_players = Role.query.filter(Role.gid == game.gid).all()
            for p in all_players:
                p.reset()
            raise GameFinished()

        if GameEnum.GROUP_TYPE_GODS not in groups and GameEnum.GROUP_TYPE_VILLAGERS not in groups:
            publish_history(game.gid, '游戏结束，狼人阵营胜利')
            # game.status = GameEnum.GAME_STATUS_FINISHED
            StepProcessor.init_game(game)
            all_players = Role.query.filter(Role.gid == game.gid).all()
            for p in all_players:
                p.reset()
            raise GameFinished()

        # todo third party
        # todo reset game

    @staticmethod
    def init_game(game):
        game.status = GameEnum.GAME_STATUS_WAIT_TO_START
        game.end_time = datetime.utcnow() + timedelta(days=1)
        game.days = 0
        game.now_index = -1
        game.step_cnt = 0
        game.steps = []
        game.history = {}
        game.captain_pos = -1
        game.players = []
        StepProcessor._reset_history(game)


#     def get_attackable_wolf(self):
#         attackable = []
#         for r in self.roles:
#             if r.alive and GameEnum.ROLE_TYPE_ALL_WOLF in r.tags:
#                 attackable.append(r)
#         return attackable

def timeout_move_on(gid, step_cnt):
    with Game.query.with_for_update().get(gid) as game:
        if step_cnt != game.step_cnt:
            return
        StepProcessor.move_on(game)
