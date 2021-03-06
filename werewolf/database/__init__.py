from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import TypeDecorator, VARCHAR, INTEGER
from sqlalchemy.ext.mutable import MutableDict, MutableList
import json
from werewolf.utils.enums import GameEnum
from werewolf.utils.json_utils import json_hook, ExtendedJSONEncoder
from werewolf.utils.game_exceptions import GameFinished

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)

    @app.teardown_request
    def db_teardown(exception):
        if exception:
            db.session.rollback()

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()


class JSONEncodedType(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value, cls=ExtendedJSONEncoder)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value, object_hook=json_hook)
        return value


class EnumType(TypeDecorator):
    impl = INTEGER

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = value.value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = GameEnum(int(value))
        return value


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci'}
    # name 'id' is preserved!
    uid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(length=255),
                         nullable=False, unique=True, index=True)
    password = db.Column(db.String(length=255), nullable=False)
    login_token = db.Column(db.String(length=255), nullable=False, index=True)
    nickname = db.Column(db.String(length=255), nullable=False)
    avatar = db.Column(db.Integer, nullable=False)
    gid = db.Column(db.Integer, nullable=False)  # gid=-1 means not in game

    # def to_json(self) -> dict:
    #     return {'uid': self.uid,
    #             'username': self.table.username,
    #             'password': self.table.password,
    #             'login_token': self.table.login_token,
    #             'name': self.name,
    #             'avatar': self.avatar,
    #             'gid': self.gid,
    #             'ishost': self.ishost}


class Game(db.Model):
    __tablename__ = 'games'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci'}
    gid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    host_uid = db.Column(db.Integer, nullable=False)
    status = db.Column(EnumType, nullable=False)
    victory_mode = db.Column(EnumType, nullable=False)
    captain_mode = db.Column(EnumType, nullable=False)
    witch_mode = db.Column(EnumType, nullable=False)
    wolf_mode = db.Column(EnumType, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    players = db.Column(MutableList.as_mutable(JSONEncodedType(225)), nullable=False)
    cards = db.Column(MutableList.as_mutable(JSONEncodedType(1023)), nullable=False)
    days = db.Column(db.Integer, nullable=False)
    now_index = db.Column(db.Integer, nullable=False)
    step_cnt = db.Column(db.Integer, nullable=False)
    steps = db.Column(MutableList.as_mutable(JSONEncodedType(1023)), nullable=False)
    history = db.Column(MutableDict.as_mutable(JSONEncodedType(1023)), nullable=False)
    captain_pos = db.Column(db.Integer, nullable=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        db.session.commit()
        return True if exc_type is None else False

    def get_seats_cnt(self):
        cnt = len(self.cards)
        if GameEnum.ROLE_TYPE_THIEF in self.cards:
            cnt -= 2
        return cnt


class Role(db.Model):
    __tablename__ = 'roles'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci'}
    uid = db.Column(db.Integer, primary_key=True)
    gid = db.Column(db.Integer, nullable=False, index=True)  # gid=-1 means not in game
    nickname = db.Column(db.String(length=255), nullable=False)
    avatar = db.Column(db.Integer, nullable=False)
    role_type = db.Column(EnumType, nullable=False)
    group_type = db.Column(EnumType, nullable=False)
    alive = db.Column(db.Boolean, nullable=False)
    # iscaptain = db.Column(db.Boolean, nullable=False)
    voteable = db.Column(db.Boolean, nullable=False)
    speakable = db.Column(db.Boolean, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    skills = db.Column(MutableList.as_mutable(JSONEncodedType(255)), nullable=False)
    tags = db.Column(MutableList.as_mutable(JSONEncodedType(255)), nullable=False)
    args = db.Column(MutableDict.as_mutable(JSONEncodedType(255)), nullable=False)

    def reset(self):
        self.role_type = GameEnum.ROLE_TYPE_UNKNOWN
        self.group_type = GameEnum.GROUP_TYPE_UNKNOWN
        self.alive = True
        # self.iscaptain = False
        self.voteable = True
        self.speakable = True
        self.position = -1
        self.skills = []
        self.tags = []
        self.args = {}

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
            self.args = {'guard': GameEnum.TARGET_NO_ONE.value}
            self.group_type = GameEnum.GROUP_TYPE_GODS
        elif self.role_type is GameEnum.ROLE_TYPE_VILLAGER:
            self.group_type = GameEnum.GROUP_TYPE_VILLAGERS
        elif self.role_type is GameEnum.ROLE_TYPE_NORMAL_WOLF:
            self.group_type = GameEnum.GROUP_TYPE_WOLVES
            self.tags.append(GameEnum.TAG_ATTACKABLE_WOLF)
        elif self.role_type is GameEnum.ROLE_TYPE_IDIOT:
            self.args = {'exposed': False}
            self.group_type = GameEnum.GROUP_TYPE_GODS
        else:
            raise TypeError(f'Cannot prepare for role type {self.role_type}')

        # prepare for skills
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
        if GameEnum.TAG_ATTACKABLE_WOLF in self.tags:
            skills.append(GameEnum.SKILL_WOLF_KILL)
            skills.append(GameEnum.SKILL_SUICIDE)

        self.skills = skills
        return
