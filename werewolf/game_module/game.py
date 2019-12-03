# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-28 21:59:40
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 17:24:49

from __future__ import annotations

from datetime import datetime, timedelta
from flask_login import current_user
from werewolf.utils.enums import GameStatus, VictoryMode, CaptainMode, WitchMode, RoleType, TurnStep
import json
from werewolf.utils.json_utils import JsonHook, ExtendJSONEncoder, stringify_keys
from werewolf.db import db
from werewolf.game_module.role import Role
from sqlalchemy.dialects.mysql import DATETIME
import typing
from typing import List
from werewolf.game_module.game_message import GameMessage
from collections import Counter

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
    card_dict = db.Column(db.String(length=1023), nullable=False)
    days = db.Column(db.Integer, nullable=False)
    now_index = db.Column(db.Integer, nullable=False)
    repeat = db.Column(db.Integer, nullable=False)
    steps = db.Column(db.String(length=1023), nullable=False)

    # def __init__(self,
    #              host_id: int,
    #              victory_mode: int,
    #              captain_mode: int,
    #              witch_mode: int,
    #              end_time: datetime,
    #              card_dict: str,
    #              last_modified: datetime = None,
    #              status: int = GameStatus.WAIT_TO_START.value,
    #              players: str = '[]',
    #              turn: str = '{}',
    #              gid: int = None):
    #     self.gid = gid
    #     self.host_id = host_id
    #     self.status = status
    #     self.victory_mode = victory_mode
    #     self.captain_mode = captain_mode
    #     self.witch_mode = witch_mode
    #     self.players = players
    #     self.end_time = end_time
    #     self.last_modified = last_modified
    #     self.turn = turn
    #     self.card_dict = card_dict

    # def __init__(self, host_id: int, victory_mode: VictoryMode, roles: List[Role], end_time: datetime, turn: Turn,
    #              card_dict: dict,
    #              captain_mode: CaptainMode, witch_mode: WitchMode, audio: list, history: list, gid: int = None,
    #              status: GameStatus = GameStatus.WAIT_TO_START):
    #     self.gid = gid
    #     self.host_id = host_id
    #     self.status = status.value
    #     self.victory_mode = victory_mode.value
    #     self.captain_mode = captain_mode.value
    #     self.witch_mode = witch_mode.value
    #     if roles is None:
    #         roles = []
    #     self.roles = json.dumps([role.uid for role in roles], cls=ExtendJSONEncoder)
    #     self.end_time = end_time
    #     self.turn = json.dumps(turn, cls=ExtendJSONEncoder)
    #     self.card_dict = json.dumps(stringify_keys(card_dict), cls=ExtendJSONEncoder)
    #     self.audio = json.dumps(audio, cls=ExtendJSONEncoder)
    #     self.history = json.dumps(history, cls=ExtendJSONEncoder)
    #     # self.roles = json.dumps(roles, cls=ExtendJSONEncoder)

    # @classmethod
    # def create_new_game_table(cls, host_id: int, victory_mode: VictoryMode, card_dict: dict,
    #                           captain_mode: CaptainMode, witch_mode: WitchMode):
    #     turn = Turn(card_dict=card_dict, captain_mode=captain_mode)
    #     game_table = GameTable(host_id=host_id, victory_mode=victory_mode,
    #                            roles=[], end_time=datetime.utcnow() + timedelta(days=1), turn=turn, card_dict=card_dict,
    #                            captain_mode=captain_mode, witch_mode=witch_mode, audio=[],
    #                            history=[])
    #     return game_table


class Game(object):
    def __init__(self, table: GameTable = None, roles: List[Role] = None, steps: list = None, card_dict: dict = None,
                 last_modified: datetime = None):
        self.table = table
        self._roles = roles
        self._steps = steps
        self._card_dict = card_dict
        self._last_modified = last_modified
        # def __init__(self, gid: int = -1, host_id: int = -1, status: GameStatus = GameStatus.UNKNOWN,
        #              victory_mode: VictoryMode = VictoryMode.UNKNOWN,
        #              captain_mode: CaptainMode = CaptainMode.UNKNOWN,
        #              witch_mode: WitchMode = WitchMode.UNKNOWN,
        #              roles: list = None,
        #              turn: Turn = None, card_dict: dict = None, audio: list = None, history: list = None,
        #              table: GameTable = None):

    @property
    def gid(self):
        return self.table.gid

    # @gid.setter
    # def gid(self, gid: int):
    #     self.table.gid = gid

    @property
    def host_id(self):
        return self.table.host_id

    # @host_id.setter
    # def host_id(self, host_id: int):
    #     self.table.host_id = host_id

    @property
    def status(self):
        return GameStatus(self.table.status)

    @status.setter
    def status(self, status: GameStatus):
        self.table.status = status.value

    @property
    def victory_mode(self):
        return VictoryMode(self.table.victory_mode)

    # @victory_mode.setter
    # def victory_mode(self, victory_mode: VictoryMode):
    #     self.table.victory_mode = victory_mode.value

    @property
    def captain_mode(self):
        return CaptainMode(self.table.captain_mode)

    @property
    def witch_mode(self):
        return WitchMode(self.table.witch_mode)

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
    def steps(self, steps: list):
        self.table._steps = steps

    @property
    def card_dict(self):
        return self._card_dict

    #
    # def _sync_to_table(self):
    #     if self.table is None:
    #         return
    #     self.table.gid = self.gid
    #     self.table.host_id = self.host_id
    #     self.table.status = self.status.value
    #     self.table.victory_mode = self.victory_mode.value
    #     self.table.captain_mode = self.captain_mode.value
    #     self.table.witch_mode = self.witch_mode.value
    #     self.table.roles = str([role.uid for role in self.roles])
    #     self.table.turn = json.dumps(self.turn, cls=ExtendJSONEncoder)
    #     self.table.card_dict = json.dumps(stringify_keys(self.card_dict), cls=ExtendJSONEncoder)
    #     self.table.audio = json.dumps(self.audio, cls=ExtendJSONEncoder)
    #     self.table.history = json.dumps(self.history, cls=ExtendJSONEncoder)
    #
    # def _sync_from_talbe(self):
    #     if self.table is None:
    #         return
    #     self.gid = self.table.gid
    #     self.host_id = self.table.host_id
    #     self.status = GameStatus(self.table.status)
    #     self.victory_mode = VictoryMode(self.table.victory_mode)
    #     self.captain_mode = CaptainMode(self.table.captain_mode)
    #     self.witch_mode = WitchMode(self.table.witch_mode)
    #     uids = json.loads(self.table.roles, object_hook=JsonHook())
    #     self.roles = []
    #     for uid in uids:
    #         new_role = Role.get_player_by_uid(uid)
    #         self.roles.append(new_role)
    #     current_user.role = None
    #     for r in self.roles:
    #         if r.uid == current_user.uid:
    #             current_user.role = r
    #             break

    # def __setattr__(self, name, value):
    #     if hasattr(self, 'table') and self.table is not None and name != 'table':
    #         if name in ['status', 'victory_mode', 'captain_mode', 'witch_mode']:
    #             self.table.__setattr__(name, value.value)
    #         elif name in ['turn', 'card_dict', 'audio', 'history']:
    #             self.table.__setattr__(name, json.dumps(value, cls=ExtendJSONEncoder))
    #         elif name == 'roles':
    #             self.table.__setattr__(name, str([role.uid for role in value]))
    #         else:
    #             self.table.__setattr__(name, value)
    #     return super().__setattr__(name, value)

    @staticmethod
    def create_new_game(host: User, victory_mode: VictoryMode, card_dict: dict, captain_mode: CaptainMode,
                        witch_mode: WitchMode):
        steps = Game._get_init_steps(card_dict, captain_mode)
        game_table = GameTable(host_id=host.uid,
                               status=GameStatus.WAIT_TO_START.value,
                               victory_mode=victory_mode.value,
                               roles='[]',
                               end_time=datetime.utcnow() + timedelta(days=1),
                               card_dict=json.dumps(stringify_keys(card_dict), cls=ExtendJSONEncoder),
                               captain_mode=captain_mode.value,
                               witch_mode=witch_mode.value,
                               days=1,
                               now_index=-1,
                               repeat=0,
                               steps=json.dumps(steps, cls=ExtendJSONEncoder))
        db.session.add(game_table)
        db.session.commit()
        game = Game(table=game_table, roles=[], steps=steps, card_dict=card_dict,
                    last_modified=game_table.last_modified)
        return game

    # @staticmethod
    # def create_game_from_table( game_table):
    #     uids = json.loads(game_table.roles, object_hook=JsonHook())
    #     roles = []
    #     for uid in uids:
    #         new_role = Role.get_player_by_uid(uid)
    #         roles.append(new_role)
    #
    #     game = Game(gid=game_table.gid, host_id=game_table.host_id, status=GameStatus(game_table.status),
    #                 victory_mode=VictoryMode(game_table.victory_mode),
    #                 captain_mode=CaptainMode(game_table.captain_mode),
    #                 witch_mode=WitchMode(game_table.witch_mode),
    #                 roles=roles,
    #                 turn=json.loads(game_table.turn, object_hook=JsonHook(Turn)),
    #                 card_dict=json.loads(game_table.card_dict, object_hook=JsonHook('card_dict')),
    #                 audio=json.loads(game_table.audio, object_hook=JsonHook()),
    #                 history=json.loads(game_table.history, object_hook=JsonHook()), table=game_table)
    #     return game

    @staticmethod
    def create_game_from_table(game_table):
        if game_table and datetime.utcnow() < game_table.end_time:
            uid_list = json.loads(game_table.roles, object_hook=JsonHook())
            roles = []
            for uid in uid_list:
                r = Role.get_role_by_uid(uid)
                roles.append(r)
            steps = json.loads(game_table.steps, object_hook=JsonHook())
            card_dict = json.loads(game_table.card_dict, object_hook=JsonHook('card_dict'))
            return Game(table=game_table, roles=roles, steps=steps, card_dict=card_dict,
                        last_modified=game_table.last_modified)
        else:
            return None

    @staticmethod
    def get_game_by_gid(gid):
        if gid is None or gid == -1:
            return None

        game_table = GameTable.query.get(gid)
        return Game.create_game_from_table(game_table)

    def commit(self) -> (bool, GameMessage):
        assert self._last_modified == self.table.last_modified
        self.table.roles = json.dumps([r.uid for r in self.roles], cls=ExtendJSONEncoder)
        self.table.steps = json.dumps(self.steps, cls=ExtendJSONEncoder)
        self.table.card_dict = json.dumps(stringify_keys(self.card_dict), cls=ExtendJSONEncoder)
        db.session.add(self.table)
        db.session.commit()
        return True, None

    # def commit(self, lock=False, func=None) -> (bool, GameMessage):
    #     if not lock:
    #         self._sync_to_table()
    #         db.session.add(self.table)
    #         db.session.commit()
    #         return True, None
    #     else:
    #         new_table = GameTable.query.with_for_update().get(self.gid)
    #         if new_table is None:
    #             return False, GameMessage('GAME_NOT_EXIST')
    #         else:
    #             self.table = new_table
    #             self._sync_from_talbe()
    #             success, message = func(self)
    #             self._sync_to_table()
    #             db.session.commit()
    #             return success, message

    def get_seat_num(self):
        cnt = sum(Counter(self.card_dict).values())
        if RoleType.THIEF in self.card_dict:
            cnt -= 2
        return cnt

    def get_role_by_pos(self):
        pass

    def get_role_by_uid(self, uid):
        for r in self.roles:
            if r.uid == uid:
                return r
        else:
            return None

    @staticmethod
    def _get_init_steps(card_dict, captain_mode):
        return Game._reset_steps(1, card_dict, captain_mode)

    @staticmethod
    def _reset_steps(day, card_dict, captain_mode):
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

        return steps

# if not user_table.login_token:
#     user_table.login_token = generate_login_token(username)
#     db.session.commit()
# else:
#     # 已经登录了
#     current_app.logger.info(user_table.login_token)
#     return redirect(url_for('werewolf_api.logout'))
