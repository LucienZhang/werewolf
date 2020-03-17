from werewolf.db import db
from werewolf.utils.enums import GameEnum, EnumMember
import json
from werewolf.utils.json_utils import ExtendedJSONEncoder, json_hook
from copy import deepcopy





class Role(object):
    """Base Class"""

    def __init__(self, table: RoleTable, skills: list = None, tags: list = None, args: dict = None):
        self.table = table
        if skills is None:
            self._skills = []
        else:
            self._skills = skills
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
                'skills': [[skill.name, skill.message] for skill in self.skills],
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
    def skills(self):
        return self._skills

    @skills.setter
    def skills(self, skills: list):
        self._skills = skills

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
    def get_role_by_uid(uid):
        if uid < 0:
            return None
        role_table = RoleTable.query.get(uid)
        if role_table is not None:
            skills = json.loads(role_table.skills, object_hook=json_hook)
            tags = json.loads(role_table.tags, object_hook=json_hook)
            args = json.loads(role_table.args, object_hook=json_hook)
            return Role(role_table, skills, tags, args)
        else:
            return None

    def commit(self) -> (bool, GameEnum):
        self.table.skills = json.dumps(self._skills, cls=ExtendedJSONEncoder)
        self.table.tags = json.dumps(self._tags, cls=ExtendedJSONEncoder)
        self.table.args = json.dumps(self._args, cls=ExtendedJSONEncoder)
        db.session.add(self.table)
        db.session.commit()
        return True, None

    def prepare(self, captain_mode):
        if self.role_type is GameEnum.ROLE_TYPE_SEER:
            self.group_type = GameEnum.GROUP_TYPE_GODS
        elif self.role_type is GameEnum.ROLE_TYPE_WITCH:
            self.args = {'elixir': True, 'toxic': True}
            self.group_type = GameEnum.GROUP_TYPE_GODS
        elif self.role_type is GameEnum.ROLE_TYPE_HUNTER:
            self.args = {'shootable': True}
            self.group_type = GameEnum.GROUP_TYPE_GODS
        elif self.role_type is GameEnum.ROLE_TYPE_SAVIOR:
            self.args = {'guard': GameEnum.TARGET_NO_ONE}
            self.group_type = GameEnum.GROUP_TYPE_GODS
        elif self.role_type is GameEnum.ROLE_TYPE_VILLAGER:
            self.group_type = GameEnum.GROUP_TYPE_VILLAGERS
        elif self.role_type is GameEnum.ROLE_TYPE_NORMAL_WOLF:
            self.group_type = GameEnum.GROUP_TYPE_WOLVES
            self.tags.append(GameEnum.ROLE_TYPE_ALL_WOLF)
        elif self.role_type is GameEnum.ROLE_TYPE_IDIOT:
            self.args = {'exposed': False}
            self.group_type = GameEnum.GROUP_TYPE_GODS
        else:
            raise TypeError(f'Cannot prepare for role type {self.role_type}')

        self._prepare_skills(captain_mode)

    def _prepare_skills(self, captain_mode):
        if self.role_type is GameEnum.ROLE_TYPE_UNKNOWN:
            self.skills = []
            return

        skills = [GameEnum.SKILL_VOTE]
        if captain_mode is GameEnum.CAPTAIN_MODE_WITH_CAPTAIN:
            skills.append(GameEnum.SKILL_CAPTAIN)

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

        self.skills = skills
        return
