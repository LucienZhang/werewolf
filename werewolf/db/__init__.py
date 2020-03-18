from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import TypeDecorator, VARCHAR, INTEGER
from sqlalchemy.ext.mutable import MutableDict, MutableList
import json
from werewolf.utils.enums import GameEnum
from werewolf.utils.json_utils import json_hook, ExtendedJSONEncoder

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)


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
    # name 'id' is preserved!
    uid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(length=255),
                         nullable=False, unique=True, index=True)
    password = db.Column(db.String(length=255), nullable=False)
    login_token = db.Column(db.String(length=255), nullable=False, index=True)
    nickname = db.Column(db.String(length=255), nullable=False)
    avatar = db.Column(db.Integer, nullable=False)
    gid = db.Column(db.Integer, nullable=False)  # gid=-1 means not in game


class Game(db.Model):
    __tablename__ = 'games'
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
    captain_uid = db.Column(db.Integer, nullable=False)

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
    uid = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(length=255), nullable=False)
    role_type = db.Column(EnumType, nullable=False)
    group_type = db.Column(EnumType, nullable=False)
    alive = db.Column(db.Boolean, nullable=False)
    iscaptain = db.Column(db.Boolean, nullable=False)
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
        self.iscaptain = False
        self.voteable = True
        self.speakable = True
        self.position = -1
        self.skills = []
        self.tags = []
        self.args = {}
