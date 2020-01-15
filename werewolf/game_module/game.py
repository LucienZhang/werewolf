from __future__ import annotations

from datetime import datetime, timedelta
from werewolf.utils.enums import GameEnum, EnumMember
import json
from werewolf.utils.json_utils import json_hook, ExtendedJSONEncoder
from werewolf.db import db
from werewolf.game_module.role import Role
from sqlalchemy.dialects.mysql import DATETIME
import typing
from typing import List
from werewolf.utils.publisher import publish_music, publish_history
from werewolf.utils.scheduler import scheduler
import collections
from copy import deepcopy

if typing.TYPE_CHECKING:
    from werewolf.game_module.user import User


class GameTable(db.Model):
    __tablename__ = 'game'
    gid = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    host_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    victory_mode = db.Column(db.Integer, nullable=False)
    captain_mode = db.Column(db.Integer, nullable=False)
    witch_mode = db.Column(db.Integer, nullable=False)
    roles = db.Column(db.String(length=255), nullable=False)
    end_time = db.Column(DATETIME(fsp=3), nullable=False)
    last_modified = db.Column(db.TIMESTAMP(True), nullable=False)
    # turn = db.Column(db.String(length=1023), nullable=False)
    cards = db.Column(db.String(length=1023), nullable=False)
    days = db.Column(db.Integer, nullable=False)
    now_index = db.Column(db.Integer, nullable=False)
    repeat = db.Column(db.Integer, nullable=False)
    steps = db.Column(db.String(length=1023), nullable=False)
    history = db.Column(db.String(length=1023), nullable=False)


class Game(object):
    def __init__(self, table: GameTable = None, roles: List[Role] = None, steps: dict = None, cards: list = None,
                 last_modified: datetime = None, history: dict = None):
        self.table = table
        if roles is None:
            self._roles = []
        else:
            self._roles = roles
        if steps is None:
            self._steps = {}
        else:
            self._steps = steps
        self._cards = cards
        if history is None:
            self._history = {}
        else:
            self._history = history
        self._last_modified = last_modified

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commit()
        return True if exc_type is None else False

    def to_json(self) -> dict:
        return {'gid': self.gid,
                'host_id': self.host_id,
                'status': self.status.name,
                'victory_mode': self.victory_mode.name,
                'captain_mode': self.captain_mode.name,
                'witch_mode': self.witch_mode.name,
                'roles': [role.uid for role in self.roles],
                'end_time': str(self.table.end_time),
                'last_modified': str(self.table.last_modified),
                'cards': [card.name for card in self.cards],
                'days': self.days,
                'now_index': self.now_index,
                'repeat': self.repeat,
                'steps': {
                    'global_steps': self.steps['global_steps'],
                    'step_list': [step.name for step in self.steps['step_list']]
                },
                'history': self.history}

    @property
    def gid(self):
        return self.table.gid

    @property
    def host_id(self):
        return self.table.host_id

    @property
    def status(self):
        return GameEnum(self.table.status)

    @status.setter
    def status(self, status: EnumMember):
        self.table.status = status.value

    @property
    def victory_mode(self):
        return GameEnum(self.table.victory_mode)

    @property
    def captain_mode(self):
        return GameEnum(self.table.captain_mode)

    @property
    def witch_mode(self):
        return GameEnum(self.table.witch_mode)

    @property
    def roles(self):
        return self._roles

    @property
    def days(self):
        return self.table.days

    @days.setter
    def days(self, days: int):
        self.table.days = days

    @property
    def now_index(self):
        return self.table.now_index

    @now_index.setter
    def now_index(self, now_index: int):
        self.table.now_index = now_index

    @property
    def repeat(self):
        return self.table.repeat

    @repeat.setter
    def repeat(self, repeat: int):
        self.table.repeat = repeat

    @property
    def steps(self):
        return self._steps

    @steps.setter
    def steps(self, steps: dict):
        """
        {
            'global_steps':0,
            'step_list':[EnumMember,...]
        }
        """
        self.table._steps = steps

    @property
    def cards(self):
        return self._cards

    @property
    def history(self):
        """
            pos: -1=no one, -2=not acted
            {
                'wolf_kill':{wolf_pos:target_pos,...},
                'wolf_kill_decision':pos
                'elixir':True / False,
                'guard':pos,
                'toxic':pos,
                'discover':pos
            }
        """
        return self._history

    @history.setter
    def history(self, history: dict):
        self.table._history = history

    @staticmethod
    def create_new_game(host: User, victory_mode: GameEnum, cards: list, captain_mode: GameEnum,
                        witch_mode: GameEnum):
        steps = Game._get_init_steps(cards, captain_mode)
        game_table = GameTable(host_id=host.uid,
                               status=GameEnum.GAME_STATUS_WAIT_TO_START.value,
                               victory_mode=victory_mode.value,
                               roles='[]',
                               end_time=datetime.utcnow() + timedelta(days=1),
                               cards=json.dumps(cards, cls=ExtendedJSONEncoder),
                               captain_mode=captain_mode.value,
                               witch_mode=witch_mode.value,
                               days=1,
                               now_index=-1,
                               repeat=0,
                               steps=json.dumps(steps, cls=ExtendedJSONEncoder),
                               history='{}')
        db.session.add(game_table)
        db.session.commit()
        game = Game(table=game_table, roles=None, steps=steps, cards=cards,
                    last_modified=game_table.last_modified, history=None)
        return game

    # @staticmethod
    # def create_game_from_table(game_table):
    #     if game_table and datetime.utcnow() < game_table.end_time:
    #         uid_list = json.loads(game_table.roles)
    #         roles = []
    #         for uid in uid_list:
    #             r = Role.get_role_by_uid(uid)
    #             roles.append(r)
    #         steps = json.loads(game_table.steps, object_hook=json_hook)
    #         cards = json.loads(game_table.cards, object_hook=json_hook)
    #         return Game(table=game_table, roles=roles, steps=steps, cards=cards,
    #                     last_modified=game_table.last_modified)
    #     else:
    #         return None

    @staticmethod
    def get_game_by_gid(gid, lock=False, load_roles=True):
        if gid is None or gid == -1:
            return None
        if not lock:
            game_table = GameTable.query.get(gid)
            if game_table and datetime.utcnow() < game_table.end_time:
                roles = []
                if load_roles:
                    uid_list = json.loads(game_table.roles)
                    for uid in uid_list:
                        r = Role.get_role_by_uid(uid)
                        roles.append(r)
                steps = json.loads(game_table.steps, object_hook=json_hook)
                cards = json.loads(game_table.cards, object_hook=json_hook)
                history = json.loads(game_table.history)
                return Game(table=game_table, roles=roles, steps=steps, cards=cards,
                            history=history,
                            last_modified=game_table.last_modified)
            else:
                return None
        else:
            game_table = GameTable.query.with_for_update().get(gid)
            if game_table and datetime.utcnow() < game_table.end_time:
                roles = []
                if load_roles:
                    uid_list = json.loads(game_table.roles)
                    for uid in uid_list:
                        r = Role.get_role_by_uid(uid)
                        roles.append(r)
                steps = json.loads(game_table.steps, object_hook=json_hook)
                cards = json.loads(game_table.cards, object_hook=json_hook)
                history = json.loads(game_table.history)
                return Game(table=game_table, roles=roles, steps=steps, cards=cards,
                            history=history,
                            last_modified=game_table.last_modified)
            else:
                db.session.commit()
                return None

    def commit(self) -> (bool, GameEnum):
        assert self._last_modified == self.table.last_modified
        self.table.roles = json.dumps([r.uid for r in self.roles], cls=ExtendedJSONEncoder)
        self.table.steps = json.dumps(self.steps, cls=ExtendedJSONEncoder)
        self.table.cards = json.dumps(self.cards, cls=ExtendedJSONEncoder)
        self.table.history = json.dumps(self.history)
        db.session.add(self.table)
        db.session.commit()
        return True, None

    def get_seat_num(self):
        cnt = len(self.cards)
        if GameEnum.ROLE_TYPE_THIEF in self.cards:
            cnt -= 2
        return cnt

    def get_role_by_pos(self, pos):
        pos = int(pos)
        if pos < 0:
            return None
        for r in self.roles:
            if r.position == pos:
                return r
        else:
            raise KeyError(f'Cannot find role with pos={pos}')

    def get_role_by_uid(self, uid, with_index=False):
        for i, r in enumerate(self.roles):
            if r.uid == uid:
                return (i, r) if with_index else r
        else:
            return (None, None) if with_index else None

    @staticmethod
    def _get_init_steps(cards, captain_mode) -> dict:
        return {
            'global_steps': 0,
            'step_list': Game._reset_step_list(1, cards, captain_mode)
        }

    @staticmethod
    def _reset_step_list(day, cards, captain_mode) -> list:
        step_list = []
        if day == 1 and GameEnum.ROLE_TYPE_THIEF in cards:
            pass
        if day == 1 and GameEnum.ROLE_TYPE_CUPID in cards:
            pass
        # TODO: 恋人互相确认身份
        step_list.append(GameEnum.TURN_STEP_TURN_NIGHT)
        step_list.append(GameEnum.ROLE_TYPE_ALL_WOLF)
        step_list.append(GameEnum.ROLE_TYPE_SEER)
        step_list.append(GameEnum.ROLE_TYPE_WITCH)
        step_list.append(GameEnum.ROLE_TYPE_SAVIOR)
        step_list.append(GameEnum.TURN_STEP_CHECK_VICTORY)
        step_list.append(GameEnum.TURN_STEP_TURN_DAY)
        if day == 1 and captain_mode is GameEnum.CAPTAIN_MODE_WITH_CAPTAIN:
            step_list.append(GameEnum.TURN_STEP_ELECT)
            step_list.append(GameEnum.TURN_STEP_TALK)
            step_list.append(GameEnum.TURN_STEP_VOTE_FOR_CAPTAIN)
        step_list.append(GameEnum.TURN_STEP_ANNOUNCE_AND_TALK)
        # step_list.append(GameEnum.TURN_STEP_TURN_NIGHT)

        return step_list

    def go_next_step(self) -> (bool, GameEnum):
        self.steps['global_steps'] += 1

        if self.repeat > 0:
            self.repeat -= 1
        else:
            self.now_index += 1

        if self.now_index >= len(self.steps['step_list']):
            self.now_index = 0
            self.days += 1
            self.steps['step_list'] = Game._reset_step_list(self.days, self.cards, self.captain_mode)

        # current step
        now = self.current_step()
        if now is GameEnum.TURN_STEP_TURN_NIGHT:
            publish_music('night_start_voice', 'night_bgm', f'{self.gid}-host')
            self.status = GameEnum.GAME_STATUS_NIGHT
            return self.go_next_step()
        elif now is GameEnum.ROLE_TYPE_ALL_WOLF:
            publish_music('wolf_start_voice', 'wolf_bgm', f'{self.gid}-host')
            # todo: add random job if there is not wolf (third party situation)
            scheduler.add_job(id=f'{self.gid}_WOLF_KILL', func=action_timeout,
                              args=(self.gid, self.steps['global_steps']),
                              next_run_time=datetime.now() + timedelta(seconds=30))
            return True, None

    def current_step(self):
        return self.steps['step_list'][self.now_index]

    def insert_step(self, step):
        self.steps['step_list'].insert(self.now_index + 1, step)
        return

    def get_alive_roles(self, role_type=None):
        roles = []
        for r in self.roles:
            if not r.alive:
                continue
            elif role_type is not None and r.role_type is not role_type:
                continue
            else:
                roles.append(r)
        return roles

    def _reset_history(self):
        pass

    def calculate_result(self):
        dead = set()
        # wolf kill
        targets = collections.Counter([t for _, t in self.history['wolf_kill']])
        wolf_kill_pos = targets.most_common(1)
        if not wolf_kill_pos:
            wolf_kill_pos = -1
        else:
            wolf_kill_pos = wolf_kill_pos[0][0]
        elixir = self.history['elixir']
        guard = self.history['guard']
        killed = True
        if elixir:
            killed = not killed
        if guard == wolf_kill_pos:
            killed = not killed
        if killed:
            dead.add(wolf_kill_pos)
        toxic = self.history['toxic']
        dead.add(toxic)
        # todo others
        dead = list(dead)
        dead.sort()
        for p in dead:
            r = self.get_role_by_pos(p)
            r.alive = False
            r.commit()
        publish_history(GameEnum.GAME_MESSAGE_DIE_IN_NIGHT.message.format('，'.join(dead)), str(self.gid))
        # else:
        # role = self.get_role_by_pos(die_pos)
        # role.alive = False
        # role.commit()
        # game.go_next_step()
        # game.commit()


def action_timeout(gid, global_step_num):
    game = Game.get_game_by_gid(gid)
    if global_step_num != game.steps['global_steps']:
        return
    game.go_next_step()
    game.commit()
    return

# if self.now == len(self.steps) - 1:
#             self._reset(card_dict, captain_mode)
#         else:
#             self.now += 1
#         return self.current_step()
