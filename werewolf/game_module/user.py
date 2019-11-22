# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-28 22:05:35
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 16:17:38

from dataclasses import dataclass
from werewolf.game_module.game import Game
# from app.werewolf.player import Player
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
    uid = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(length=255), nullable=False, unique=True, index=True)
    password = db.Column(db.String(length=255), nullable=False)
    login_token = db.Column(db.String(length=255), index=True)
    name = db.Column(db.String(length=255), nullable=False)
    avatar = db.Column(db.Integer, nullable=False)
    gid = db.Column(db.Integer, nullable=False)
    # player = db.Column(db.String(length=255))
    ishost = db.Column(db.Boolean, nullable=False)

    # role = db.Column(db.String(length=255))
    # position = db.Column(db.Integer, nullable=False)
    # history = db.Column(db.String(length=255))

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
        # self.role = json.dumps(role, cls=ExtendJSONEncoder)
        # self.position = position
        # self.history = history

    # @classmethod
    # def create_new_user_table(cls, username, password, name, avatar):
    #     user_table = UserTable(username=username, password=password, name=name, avatar=avatar)
    #     return user_table


@dataclass
class User(UserMixin):
    uid: int = -1  # user id
    # username: str = ""
    # password: str = ""
    name: str = "New Player"
    avatar: int = 0
    game: Game = None
    # player: Player = None
    ishost: bool = False
    role: Role = None
    # position: int = -1
    # history: str = ""
    table: UserTable = None

    def _sync_to_table(self):
        if self.table is None:
            return
        self.table.uid = self.uid
        self.table.name = self.name
        self.table.avatar = self.avatar
        self.table.gid = self.game.gid
        self.table.ishost = self.ishost

    def _sync_from_table(self):
        if self.table is None:
            return
        self.uid = self.table.uid
        self.name = self.table.name
        self.avatar = self.table.avatar
        self.ishost = self.table.ishost

    # def __setattr__(self, name, value):
    #     if hasattr(self, 'table') and self.table is not None and name in self.__dict__ and name not in ['table', 'id', 'role']:
    #         if name == 'game' and value is not None:
    #             self.table.__setattr__('gid', value.gid)
    #         else:
    #             self.table.__setattr__(name, value)
    #     return super().__setattr__(name, value)

    @classmethod
    def create_user_from_table(cls, user_table, role=None):
        user = User(uid=user_table.uid, name=user_table.name, avatar=user_table.avatar, ishost=user_table.ishost,
                    table=user_table)
        user.id = user_table.login_token
        user.game = Game.get_game_by_gid(user_table.gid)
        if role is not None:
            user.role = role
        else:
            if user.game is not None:
                for r in user.game.roles:
                    if r.uid == user.uid:
                        user.role = r
                        break
                else:
                    user.role = Role.get_role_by_uid(user_table.uid)
            else:
                pass  # no role if no game
        return user

    @classmethod
    def create_new_user(cls, username, password, name, avatar):
        if UserTable.query.filter_by(username=username).first() is not None:
            # username exists
            return None
        user_table = UserTable(username=username, password=password, name=name, avatar=avatar)
        db.session.add(user_table)
        db.session.commit()
        role = Role.create_new_role(user_table.uid)
        user = User.create_user_from_table(user_table, role=role)
        return user

    @classmethod
    def get_user_by_uid(cls, uid):
        user_table = UserTable.query.get(uid)
        if user_table is not None:
            return User.create_user_from_table(user_table)
        else:
            return None

    @classmethod
    def get_user_by_token(cls, login_token):
        if not login_token:
            return None
        user_table = UserTable.query.filter_by(login_token=login_token).first()
        if user_table is not None:
            return User.create_user_from_table(user_table)
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
            # TODO: if already in, redirect to game
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

    def commit(self):
        self._sync_to_table()
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
