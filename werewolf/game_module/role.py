from werewolf.db import db
from werewolf.utils.enums import GameEnum, EnumMember
import json
from werewolf.utils.json_utils import ExtendedJSONEncoder, json_hook
from copy import deepcopy


class RoleTable(db.Model):
    __tablename__ = 'role'
    uid = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(length=255), nullable=False)
    role_type = db.Column(db.Integer)
    group_type = db.Column(db.Integer)
    alive = db.Column(db.Boolean)
    iscaptain = db.Column(db.Boolean)
    voteable = db.Column(db.Boolean)
    speakable = db.Column(db.Boolean)
    position = db.Column(db.Integer)
    tags = db.Column(db.String(length=255), nullable=False)
    args = db.Column(db.String(length=255), nullable=False)

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


class Role(object):
    """Base Class"""

    def __init__(self, table: RoleTable, tags: list = None, args: dict = None):
        self.table = table
        if tags is None:
            self._tags = []
        else:
            self._tags = tags
        if args is None:
            self._args = {}
        else:
            self._args = args

    def to_json(self) -> dict:
        return {'uid': self.uid,
                'name': self.name,
                'role_type': [self.role_type.name, self.role_type.message],
                'group_type': self.group_type.name,
                'alive': self.alive,
                'iscaptain': self.iscaptain,
                'voteable': self.voteable,
                'speakable': self.speakable,
                'position': self.position,
                'skills': [[skill.name, skill.message] for skill in self.get_skills()],
                'tags': [tag.name for tag in self.tags],
                'args': self.args}

    @property
    def uid(self):
        return self.table.uid

    @property
    def name(self):
        return self.table.name

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
        return self._tags

    @tags.setter
    def tags(self, tags: list):
        self._tags = tags

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, args: dict):
        self._args = args

    @staticmethod
    def create_new_role(uid, name):
        role_table = RoleTable.query.get(uid)
        if role_table is None:
            role_table = RoleTable(uid=uid, name=name, tags='[]', args='{}')
            role_table.reset()
        else:
            role_table.name = name
            role_table.reset()
        db.session.add(role_table)
        db.session.commit()
        tags = json.loads(role_table.tags, object_hook=json_hook)
        args = json.loads(role_table.args, object_hook=json_hook)
        role = Role(role_table, tags=tags, args=args)
        return role

    @staticmethod
    def get_role_by_uid(uid):
        role_table = RoleTable.query.get(uid)
        if role_table is not None:
            tags = json.loads(role_table.tags, object_hook=json_hook)
            args = json.loads(role_table.args, object_hook=json_hook)
            return Role(role_table, tags, args)
        else:
            return None

    def commit(self) -> (bool, GameEnum):
        self.table.tags = json.dumps(self._tags, cls=ExtendedJSONEncoder)
        self.table.args = json.dumps(self._args, cls=ExtendedJSONEncoder)
        db.session.add(self.table)
        db.session.commit()
        return True, None

    def prepare(self):
        if self.role_type is GameEnum.ROLE_TYPE_SEER:
            self.tags.append(GameEnum.GROUP_TYPE_GODS)
        elif self.role_type is GameEnum.ROLE_TYPE_WITCH:
            self.args = {'elixir': True, 'toxic': True}
            self.tags.append(GameEnum.GROUP_TYPE_GODS)
        elif self.role_type is GameEnum.ROLE_TYPE_HUNTER:
            self.args = {'shootable': True}
            self.tags.append(GameEnum.GROUP_TYPE_GODS)
        elif self.role_type is GameEnum.ROLE_TYPE_SAVIOR:
            self.args = {'guard': GameEnum.TARGET_NO_ONE}
            self.tags.append(GameEnum.GROUP_TYPE_GODS)
        elif self.role_type is GameEnum.ROLE_TYPE_VILLAGER:
            self.tags.append(GameEnum.GROUP_TYPE_VILLAGERS)
        elif self.role_type is GameEnum.ROLE_TYPE_NORMAL_WOLF:
            self.tags.append(GameEnum.GROUP_TYPE_WOLVES)
        else:
            raise TypeError(f'Cannot prepare for role type {self.role_type}')

    def get_skills(self):
        if self.role_type is GameEnum.ROLE_TYPE_UNKNOWN:
            return []

        skills = [GameEnum.SKILL_VOTE]
        if self.role_type is GameEnum.ROLE_TYPE_SEER:
            skills.append(GameEnum.SKILL_DISCOVER)
        if self.role_type is GameEnum.ROLE_TYPE_WITCH:
            skills.append(GameEnum.SKILL_WITCH)
        if self.role_type is GameEnum.ROLE_TYPE_HUNTER:
            skills.append(GameEnum.SKILL_SHOOT)
        if self.role_type is GameEnum.ROLE_TYPE_SAVIOR:
            skills.append(GameEnum.SKILL_GUARD)
        if GameEnum.ROLE_TYPE_ALL_WOLF in self.tags:
            skills.append(GameEnum.SKILL_WOLF_KILL)
        return skills
