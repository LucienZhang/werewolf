# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-28 20:38:09
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 17:26:30

from werewolf.db import db
# from werewolf.utils.enums import RoleType, GroupType
# from werewolf.utils.game_message import GameMessage
from werewolf.utils.enums import GameEnum,EnumMember
import json
from werewolf.utils.json_utils import ExtendJSONEncoder, JsonHook


class RoleTable(db.Model):
    __tablename__ = 'role'
    uid = db.Column(db.Integer, primary_key=True, nullable=False)
    role_type = db.Column(db.Integer)
    group_type = db.Column(db.Integer)
    alive = db.Column(db.Boolean)
    iscaptain = db.Column(db.Boolean)
    voteable = db.Column(db.Boolean)
    speakable = db.Column(db.Boolean)
    position = db.Column(db.Integer)
    tags = db.Column(db.String(length=255), nullable=False)
    args = db.Column(db.String(length=255), nullable=False)

    # history = db.Column(db.String(length=4095))
    #
    # def __init__(self, uid: int, role_type: RoleType = RoleType.UNKNOWN, group_type: GroupType = GroupType.UNKNOWN,
    #              alive: bool = True, iscaptain: bool = False, voteable: bool = True, speakable: bool = True,
    #              position: int = -1, history: list = None):
    #     self.uid = uid
    #     self.role_type = role_type.value
    #     self.group_type = group_type.value
    #     self.alive = alive
    #     self.iscaptain = iscaptain
    #     self.voteable = voteable
    #     self.speakable = speakable
    #     self.position = position
    #     if history is None:
    #         self.history = json.dumps([], cls=ExtendJSONEncoder)
    #     else:
    #         self.history = json.dumps(history, cls=ExtendJSONEncoder)

    def reset(self):
        self.role_type = GameEnum.ROLE_TYPE_UNKNOWN.value
        self.group_type = GameEnum.GROUP_TYPE_UNKNOWN.value
        self.alive = True
        self.iscaptain = False
        self.voteable = True
        self.speakable = True
        self.position = -1
        self.tags = '[]'
        self.args = '{}'
        # self.history = json.dumps([], cls=ExtendJSONEncoder)


class Role(object):
    """Base Class"""

    def __init__(self, table: RoleTable, args: dict = None):
        self.table = table
        self._args = args

    @property
    def uid(self):
        return self.table.uid

    @property
    def role_type(self):
        return GameEnum(self.table.role_type)

    @role_type.setter
    def role_type(self, role_type: EnumMember):
        self.table.role_type = role_type.value

    @property
    def group_type(self):
        return GameEnum(self.table.group_type)

    @group_type.setter
    def group_type(self, group_type: EnumMember):
        self.table.group_type = group_type.value

    @property
    def alive(self):
        return self.table.alive

    @alive.setter
    def alive(self, alive: bool):
        self.table.alive = alive

    @property
    def iscaptain(self):
        return self.table.iscaptain

    @iscaptain.setter
    def iscaptain(self, iscaptain: bool):
        self.table.iscaptain = iscaptain

    @property
    def voteable(self):
        return self.table.voteable

    @voteable.setter
    def voteable(self, voteable: bool):
        self.table.voteable = voteable

    @property
    def speakable(self):
        return self.table.speakable

    @speakable.setter
    def speakable(self, speakable: bool):
        self.table.speakable = speakable

    @property
    def position(self):
        return self.table.position

    @position.setter
    def position(self, position: int):
        self.table.position = position

    @property
    def tags(self):
        # todo
        return self.table.tags

    @tags.setter
    def tags(self, tags: int):  # todo: tags:??
        self.table.tags = tags.value

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, args: dict):
        self._args = args

    # def __init__(self, uid: int = -1, role_type: RoleType = RoleType.UNKNOWN, group_type: GroupType = GroupType.UNKNOWN,
    #              alive: bool = True, iscaptain: bool = False, voteable: bool = True, speakable: bool = True,
    #              position: int = -1, history: str = None, table: RoleTable = None):
    #     self.uid = uid
    #     self.role_type = role_type
    #     self.group_type = group_type
    #     self.alive = alive
    #     self.iscaptain = iscaptain
    #     self.voteable = voteable
    #     self.speakable = speakable
    #     self.position = position
    #     if history is None:
    #         self.history = []
    #     else:
    #         self.history = history
    #     self.table = table
    #
    # def _sync_to_table(self):
    #     if self.table is None:
    #         return
    #     self.table.uid = self.uid
    #     self.table.role_type = self.role_type.value
    #     self.table.group_type = self.group_type.value
    #     self.table.alive = self.alive
    #     self.table.iscaptain = self.iscaptain
    #     self.table.voteable = self.voteable
    #     self.table.speakable = self.speakable
    #     self.table.position = self.position
    #     self.table.history = json.dumps(self.history, cls=ExtendJSONEncoder)
    #
    # def _sync_from_table(self):
    #     if self.table is None:
    #         return
    #     self.uid = self.table.uid
    #     self.role_type = RoleType(self.table.role_type)
    #     self.group_type = GroupType(self.table.group_type)
    #     self.alive = self.table.alive
    #     self.iscaptain = self.table.iscaptain
    #     self.voteable = self.table.voteable
    #     self.speakable = self.table.speakable
    #     self.position = self.table.position
    #     self.history = json.loads(self.table.history, object_hook=JsonHook())

    # def __setattr__(self, name, value):
    #     if hasattr(self, 'table') and self.table is not None and name in self.__dict__ and name not in ['table']:
    #         if name in ['role_type', 'group_type']:
    #             self.table.__setattr__(name, value.value)
    #         elif name in ['history']:
    #             self.table.__setattr__(name, json.dumps(value, cls=ExtendJSONEncoder))
    #         else:
    #             self.table.__setattr__(name, value)
    #     return super().__setattr__(name, value)

    # def _reset(self):
    #     self.role_type = RoleType.UNKNOWN
    #     self.group_type = GroupType.UNKNOWN
    #     self.alive = True
    #     self.iscaptain = False
    #     self.voteable = True
    #     self.speakable = True
    #     self.position = -1
    #     self.history = []

    # @staticmethod
    # def create_role_from_table(role_table):
    #     role = Role(uid=role_table.uid, role_type=RoleType(role_table.role_type),
    #                 group_type=GroupType(role_table.group_type),
    #                 alive=role_table.alive, iscaptain=role_table.iscaptain, voteable=role_table.voteable,
    #                 speakable=role_table.speakable,
    #                 position=role_table.position, history=json.loads(role_table.history, object_hook=JsonHook()),
    #                 table=role_table)
    #     return role

    @staticmethod
    def create_new_role(uid):
        role_table = RoleTable.query.get(uid)
        if role_table is None:
            role_table = RoleTable(uid=uid, tags='[]', args='{}')
        else:
            role_table.reset()
        db.session.add(role_table)
        db.session.commit()
        args = json.loads(role_table.args, object_hook=JsonHook())
        role = Role(role_table, args=args)
        return role

    @staticmethod
    def get_role_by_uid(uid):
        role_table = RoleTable.query.get(uid)
        if role_table is not None:
            args = json.loads(role_table.args, object_hook=JsonHook())
            return Role(role_table, args)
        else:
            return None

    def commit(self) -> (bool, GameEnum):
        self.table.args = json.dumps(self._args, cls=ExtendJSONEncoder)
        db.session.add(self.table)
        db.session.commit()
        return True, None

    def prepare(self):
        # if self.role_type is RoleType.
        pass
    # def commit(self, lock=False, func=None) -> (bool, GameMessage):
    #     if not lock:
    #         self._sync_to_table()
    #         db.session.add(self.table)
    #         db.session.commit()
    #         return True, None
    #     else:
    #         new_table = RoleTable.query.with_for_update().get(self.uid)
    #         if new_table is None:
    #             return False, GameMessage('ROLE_NOT_EXIST')
    #         else:
    #             self.table = new_table
    #             self._sync_from_table()
    #             success, message = func(self)
    #             self._sync_to_table()
    #             db.session.commit()
    #             return success, message
