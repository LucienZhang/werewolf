from werewolf.game_module.game import Game
from flask_login import UserMixin
from werewolf.game_module.role import Role
from werewolf.db import db
from werewolf.utils.enums import GameEnum
from copy import deepcopy


class UserTable(db.Model):
    __tablename__ = 'user'
    # name 'id' is preserved!
    uid = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    username = db.Column(db.String(length=255), nullable=False, unique=True, index=True)
    password = db.Column(db.String(length=255), nullable=False)
    login_token = db.Column(db.String(length=255), index=True)
    name = db.Column(db.String(length=255), nullable=False)
    avatar = db.Column(db.Integer, nullable=False)
    gid = db.Column(db.Integer, nullable=False)  # gid=-1 means not in game
    ishost = db.Column(db.Boolean, nullable=False)


class User(UserMixin):
    def __init__(self, table: UserTable = None):
        self.table = table

    def to_json(self) -> dict:
        return {'uid': self.uid,
                'username': self.table.username,
                'password': self.table.password,
                'login_token': self.table.login_token,
                'name': self.name,
                'avatar': self.avatar,
                'gid': self.gid,
                'ishost': self.ishost}

    @property
    def uid(self):
        return self.table.uid

    @property
    def name(self):
        return self.table.name

    @name.setter
    def name(self, name: str):
        self.table.name = name

    @property
    def avatar(self):
        return self.table.avatar

    @avatar.setter
    def avatar(self, avatar: int):
        self.table.avatar = avatar

    @property
    def ishost(self):
        return self.table.ishost

    @ishost.setter
    def ishost(self, ishost: bool):
        self.table.ishost = ishost

    @property
    def gid(self):
        return self.table.gid

    @gid.setter
    def gid(self, gid: int):
        self.table.gid = gid

    @staticmethod
    def create_new_user(username, password, name, avatar):
        if UserTable.query.filter_by(username=username).first() is not None:
            # username exists
            # todo: return view
            return None
        user_table = UserTable(username=username, password=password, name=name, avatar=avatar, gid=-1, ishost=False)
        db.session.add(user_table)
        db.session.commit()
        # Role.create_new_role(user_table.uid) todo :does not need
        user = User(table=user_table)
        return user

    @staticmethod
    def get_user_by_uid(uid):
        user_table = UserTable.query.get(uid)
        if user_table is not None:
            return User(table=user_table)
        else:
            return None

    @staticmethod
    def get_user_by_token(login_token):
        if not login_token:
            return None
        user_table = UserTable.query.filter_by(login_token=login_token).first()
        if user_table is not None:
            return User(table=user_table)
        else:
            return None

    @staticmethod
    def get_user_by_username(username):
        if not username:
            return None
        user_table = UserTable.query.filter_by(username=username).first()
        if user_table is not None:
            return User(table=user_table)
        else:
            return None

    def join_game(self, gid: int) -> (bool, GameEnum):
        game = Game.get_game_by_gid(gid, lock=True)
        if game is None:
            return False, GameEnum.GAME_MESSAGE_GAME_NOT_EXIST
        if len(game.roles) >= game.get_seat_num():
            db.session.commit()
            return False, GameEnum.GAME_MESSAGE_GAME_FULL
        if game.get_role_by_uid(self.uid) is not None:
            db.session.commit()
            return False, GameEnum.GAME_MESSAGE_ALREADY_IN

        # fine to join the game
        new_role = Role.create_new_role(self.uid)
        game.roles.append(new_role)
        game.commit()
        self.gid = game.gid
        self.ishost = self.uid == game.host_id
        self.commit()
        new_role.position = len(game.roles)
        new_role.commit()
        return True, None

    def quit_game(self) -> (bool, GameEnum):
        game = Game.get_game_by_gid(self.gid)
        if game is None:
            return False, GameEnum.GAME_MESSAGE_NOT_IN_GAME
        index, my_role = game.get_role_by_uid(self.uid, with_index=True)
        if my_role is None:
            return False, GameEnum.GAME_MESSAGE_NOT_IN_GAME

        del game.roles[index]
        game.commit()

        self.ishost = False
        self.gid = -1
        self.commit()
        # TODO: role reset??
        # self.role.reset
        return True, None

    def commit(self) -> (bool, GameEnum):
        db.session.add(self.table)
        db.session.commit()
        return True, None
