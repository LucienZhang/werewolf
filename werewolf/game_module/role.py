# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-28 20:38:09
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 17:26:30

from werewolf.db import db
from werewolf.utils.enums import RoleType, GroupType
import json
from werewolf.utils.json_utils import JsonHook, ExtendJSONEncoder
from werewolf.game_module.game_message import GameMessage


class RoleTable(db.Model):
    __tablename__ = 'role'
    uid = db.Column(db.Integer, primary_key=True, nullable=False)
    role_type = db.Column(db.Integer)
    group_type = db.Column(db.Integer)
    alive = db.Column(db.Boolean)
    iscaptain = db.Column(db.Boolean)
    votable = db.Column(db.Boolean)
    speakable = db.Column(db.Boolean)
    position = db.Column(db.Integer)
    history = db.Column(db.String(length=4095))

    def __init__(self, uid: int, role_type: RoleType = RoleType.UNKNOWN, group_type: GroupType = GroupType.UNKNOWN,
                 alive: bool = True, iscaptain: bool = False, votable: bool = True, speakable: bool = True,
                 position: int = -1, history: list = None):
        self.uid = uid
        self.role_type = role_type.value
        self.group_type = group_type.value
        self.alive = alive
        self.iscaptain = iscaptain
        self.votable = votable
        self.speakable = speakable
        self.position = position
        if history is None:
            self.history = json.dumps([], cls=ExtendJSONEncoder)
        else:
            self.history = json.dumps(history, cls=ExtendJSONEncoder)

    def _reset(self):
        self.role_type = RoleType.UNKNOWN.value
        self.group_type = GroupType.UNKNOWN.value
        self.alive = True
        self.iscaptain = False
        self.votable = True
        self.speakable = True
        self.position = -1
        self.history = json.dumps([], cls=ExtendJSONEncoder)


class Role(object):
    """Base Class"""

    def __init__(self, uid: int = -1, role_type: RoleType = RoleType.UNKNOWN, group_type: GroupType = GroupType.UNKNOWN,
                 alive: bool = True, iscaptain: bool = False, votable: bool = True, speakable: bool = True,
                 position: int = -1, history: str = None, table: RoleTable = None):
        self.uid = uid
        self.role_type = role_type
        self.group_type = group_type
        self.alive = alive
        self.iscaptain = iscaptain
        self.votable = votable
        self.speakable = speakable
        self.position = position
        if history is None:
            self.history = []
        else:
            self.history = history
        self.table = table

    def _sync_to_table(self):
        if self.table is None:
            return
        self.table.uid = self.uid
        self.table.role_type = self.role_type.value
        self.table.group_type = self.group_type.value
        self.table.alive = self.alive
        self.table.iscaptain = self.iscaptain
        self.table.votable = self.votable
        self.table.speakable = self.speakable
        self.table.position = self.position
        self.table.history = json.dumps(self.history, cls=ExtendJSONEncoder)

    def _sync_from_table(self):
        if self.table is None:
            return
        self.uid = self.table.uid
        self.role_type = RoleType(self.table.role_type)
        self.group_type = GroupType(self.table.group_type)
        self.alive = self.table.alive
        self.iscaptain = self.table.iscaptain
        self.votable = self.table.votable
        self.speakable = self.table.speakable
        self.position = self.table.position
        self.history = json.loads(self.table.history, object_hook=JsonHook())

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
    #     self.votable = True
    #     self.speakable = True
    #     self.position = -1
    #     self.history = []

    @classmethod
    def create_role_from_table(cls, role_table):
        role = Role(uid=role_table.uid, role_type=RoleType(role_table.role_type), group_type=GroupType(role_table.group_type),
                    alive=role_table.alive, iscaptain=role_table.iscaptain, votable=role_table.votable, speakable=role_table.speakable,
                    position=role_table.position, history=json.loads(role_table.history, object_hook=JsonHook()), table=role_table)
        return role

    @classmethod
    def create_new_role(cls, uid):
        role_table = RoleTable.query.get(uid)
        if role_table is None:
            role_table = RoleTable(uid=uid)
        else:
            role_table._reset()
        db.session.add(role_table)
        db.session.commit()
        role = Role.create_role_from_table(role_table)
        return role

    @classmethod
    def get_role_by_uid(cls, uid):
        role_table = RoleTable.query.get(uid)
        if role_table is not None:
            return Role.create_role_from_table(role_table)
        else:
            return None

    def commit(self, lock=False, func=None)->(bool, GameMessage):
        if not lock:
            self._sync_to_table()
            db.session.add(self.table)
            db.session.commit()
            return True, None
        else:
            new_table = RoleTable.query.with_for_update().get(self.uid)
            if new_table is None:
                return False, GameMessage('ROLE_NOT_EXIST')
            else:
                self.table = new_table
                self._sync_from_table()
                success, message = func(self)
                self._sync_to_table()
                db.session.commit()
                return success, message