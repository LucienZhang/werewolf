# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-28 21:59:40
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 17:24:49

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


class Game(object):
    def __init__(self, table: GameTable = None, roles: List[Role] = None, steps: list = None, cards: list = None,
                 last_modified: datetime = None):
        self.table = table
        self._roles = roles
        self._steps = steps
        self._cards = cards
        self._last_modified = last_modified

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
    def steps(self, steps: list):
        self.table._steps = steps

    @property
    def cards(self):
        return self._cards

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
                               steps=json.dumps(steps, cls=ExtendedJSONEncoder))
        db.session.add(game_table)
        db.session.commit()
        game = Game(table=game_table, roles=[], steps=steps, cards=cards,
                    last_modified=game_table.last_modified)
        return game

    @staticmethod
    def create_game_from_table(game_table):
        if game_table and datetime.utcnow() < game_table.end_time:
            uid_list = json.loads(game_table.roles)
            roles = []
            for uid in uid_list:
                r = Role.get_role_by_uid(uid)
                roles.append(r)
            steps = json.loads(game_table.steps, object_hook=json_hook)
            cards = json.loads(game_table.cards, object_hook=json_hook)
            return Game(table=game_table, roles=roles, steps=steps, cards=cards,
                        last_modified=game_table.last_modified)
        else:
            return None

    @staticmethod
    def get_game_by_gid(gid):
        if gid is None or gid == -1:
            return None

        game_table = GameTable.query.get(gid)
        return Game.create_game_from_table(game_table)

    def commit(self) -> (bool, GameEnum):
        assert self._last_modified == self.table.last_modified
        self.table.roles = json.dumps([r.uid for r in self.roles], cls=ExtendedJSONEncoder)
        self.table.steps = json.dumps(self.steps, cls=ExtendedJSONEncoder)
        self.table.cards = json.dumps(self.cards, cls=ExtendedJSONEncoder)
        db.session.add(self.table)
        db.session.commit()
        return True, None

    def get_seat_num(self):
        cnt = len(self.cards)
        if GameEnum.ROLE_TYPE_THIEF in self.cards:
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
    def _get_init_steps(cards, captain_mode):
        return Game._reset_steps(1, cards, captain_mode)

    @staticmethod
    def _reset_steps(day, cards, captain_mode):
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

        return steps

    def go_next_step(self):  # return if need to return the answer to user
        pass
    #         if self.now == len(self.steps) - 1:
    #             self._reset(card_dict, captain_mode)
    #         else:
    #             self.now += 1
    #         return self.current_step()
