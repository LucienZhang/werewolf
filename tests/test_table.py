import sys
from pathlib import Path
import pytest
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))
from tests.env import init_table, app, db
from werewolf.db import User, Game, Role


@pytest.mark.usefixtures('init_table')
def test_user_table():
    user = User(username='username', password='password', login_token='login_token', nickname='nickname', avatar=0, gid=-1)
    db.session.add(user)
    db.session.commit()
    assert isinstance(user.uid, int)
    new_user = User.query.get(user.uid)
    assert new_user.username == 'username'
    assert new_user.password == 'password'
    assert new_user.login_token == 'login_token'
    assert new_user.nickname == 'nickname'
    assert new_user.avatar == 0
    assert new_user.gid == -1


@pytest.mark.usefixtures('init_table')
def test_game_table():
    pass


@pytest.mark.usefixtures('init_table')
def test_role_table():
    pass
