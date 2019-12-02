# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-28 22:05:35
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 16:17:38


import functools
from werewolf.game_module.game import Game
from flask_login import UserMixin
from werewolf.game_module.game import GameTable
from werewolf.game_module.role import Role
from datetime import datetime
from werewolf.db import db
import json
from werewolf.utils.json_utils import JsonHook, ExtendJSONEncoder
from werewolf.game_module.game_message import GameMessage


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

    def __init__(self, uid: int = None, username: str = None, password: str = None, login_token: str = None,
                 name: str = None,
                 avatar: int = -1, gid: int = -1, ishost: bool = False):
        self.uid = uid
        self.username = username
        self.password = password
        self.login_token = login_token
        self.name = name
        self.avatar = avatar
        self.gid = gid
        self.ishost = ishost


# def commit(func):
#     @functools.wraps(func)
#     def wrapper(self, *args, **kw):
#         func(self, *args, **kw)
#         db.session.add(self.table)
#         db.session.commit()
#
#     return wrapper


class User(UserMixin):
    def __init__(self, table: UserTable = None, game: Game = None, role=None):
        self.table = table
        self._game = game
        self._role = role

    @property
    def uid(self):
        return self.table.uid

    @uid.setter
    def uid(self, uid: int):
        self.table.uid = uid

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
    def game(self):
        return self._game

    @game.setter
    def game(self, game: Game):
        self._game = game
        self.table.gid = game.gid

    @property
    def ishost(self):
        return self.table.ishost

    @ishost.setter
    def ishost(self, ishost: bool):
        self.table.ishost = ishost

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role: Role):
        self._role = role

    # @staticmethod
    # def create_user_from_table(user_table, role=None):
    #     user = User(uid=user_table.uid, name=user_table.name, avatar=user_table.avatar, ishost=user_table.ishost,
    #                 table=user_table)
    #     user.id = user_table.login_token
    #     user.game = Game.get_game_by_gid(user_table.gid)
    #     if role is not None:
    #         user.role = role
    #     else:
    #         if user.game is not None:
    #             for r in user.game.roles:
    #                 if r.uid == user.uid:
    #                     user.role = r
    #                     break
    #             else:
    #                 user.role = Role.get_role_by_uid(user_table.uid)
    #         else:
    #             pass  # no role if no game
    #     return user

    @staticmethod
    def create_new_user(username, password, name, avatar):
        if UserTable.query.filter_by(username=username).first() is not None:
            # username exists
            return None
        user_table = UserTable(username=username, password=password, name=name, avatar=avatar)
        db.session.add(user_table)
        db.session.commit()
        role = Role.create_new_role(user_table.uid)
        user = User(table=user_table, role=role)
        return user

    @staticmethod
    def get_user_by_uid(uid):
        user_table = UserTable.query.get(uid)
        if user_table is not None:
            role = Role.get_role_by_uid(uid)
            game = Game.get_game_by_gid(user_table.gid)
            return User(table=user_table, role=role, game=game)
        else:
            return None

    @staticmethod
    def get_user_by_token(login_token):
        if not login_token:
            return None
        user_table = UserTable.query.filter_by(login_token=login_token).first()
        if user_table is not None:
            role = Role.get_role_by_uid(user_table.uid)
            game = Game.get_game_by_gid(user_table.gid)
            return User(table=user_table, role=role, game=game)
        else:
            return None

    @staticmethod
    def get_user_by_username(username):
        if not username:
            return None
        user_table = UserTable.query.filter_by(username=username).first()
        if user_table is not None:
            role = Role.get_role_by_uid(user_table.uid)
            game = Game.get_game_by_gid(user_table.gid)
            return User(table=user_table, role=role, game=game)
        else:
            return None

    def join_game(self, gid: int) -> (bool, GameMessage):
        def func(my_game):
            if len(my_game.roles) >= my_game.get_seat_num():
                return False, GameMessage('GAME_FULL')
            new_role = Role.create_new_role(self.uid)
            self.role = new_role

            # do not use append function here, otherwise the table won't be changed
            my_game.roles = my_game.roles + [self.role]
            return True, None

        game = Game.get_game_by_gid(gid)
        if game is None:
            return False, GameMessage('GAME_NOT_EXIST')
        if game.get_role_by_uid(self.uid) is not None:
            return False, GameMessage('ALREADY_IN')

        succeed, msg = game.commit(lock=True, func=func)
        if not succeed:
            return succeed, msg
        else:
            self.game = game
            self.ishost = self.uid == game.host_id
            self.role.position = len(game.roles)
            self.role.commit()
            self.commit()
            return True, None

    def quit_game(self) -> (bool, GameMessage):
        self.game = None
        self.ishost = False
        self.role

    def commit(self):
        db.session.add(self.table)
        db.session.commit()

    # def commit(self, lock=False, func=None)->(bool, str):
    #     if not lock:
    #         db.session.add(self.table)
    #         db.session.commit()
    #         return True, None
    #     else:
    #         new_table = GameTable.query.with_for_update().get(self.gid)
    #         if new_table is None:
    #             return False, GameMessage.parse('GAME_NOT_EXIST', None)
    #         else:
    #             self.table = new_table
    #             success, message = func(self)
    #             db.session.commit()
    #             return success, message
