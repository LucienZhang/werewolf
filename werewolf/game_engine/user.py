from werewolf.game_module.game import Game
from flask_login import UserMixin
from werewolf.game_module.role import Role
from werewolf.db import db
from werewolf.utils.enums import GameEnum
from copy import deepcopy





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




    

    def quit_game(self) -> (bool, GameEnum):
        game = Game.get_game_by_gid(self.gid, load_roles=True)
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
