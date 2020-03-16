import sys
from pathlib import Path
import pytest
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf import create_app
from werewolf.db import db, UserTable, GameTable, RoleTable

app = create_app('test')
app.testing = True
app.app_context().push()


@pytest.fixture(scope='module')
def init_table():
    db.drop_all()
    db.create_all()


def test_user_table(init_table):
    user = UserTable(username='username', password='password', login_token='login_token', nickname='nickname', avatar=0, gid=-1)
    db.session.add(user)
    db.session.commit()
    assert isinstance(user.uid, int)
    new_user = UserTable.query.get(user.uid)
    assert new_user.username == 'username'
    assert new_user.password == 'password'
    assert new_user.login_token == 'login_token'
    assert new_user.nickname == 'nickname'
    assert new_user.avatar == 0
    assert new_user.gid == -1


def test_game_table(init_table):
    pass


def test_role_table(init_table):
    pass
