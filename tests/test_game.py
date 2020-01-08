import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf import create_app
from werewolf.utils.enums import GameEnum

app = create_app()
app.testing = True


@pytest.fixture
def account_client():
    with app.test_client() as account_client:
        yield account_client


def login(client, username, password):
    return client.post('/werewolf/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def logout(client):
    return client.get('/werewolf/logout', follow_redirects=True)


@pytest.mark.login
def test_login_logout(account_client):
    rv = login(account_client, 'account_client', 'account_client')
    assert rv.status == '200 OK'
    rv = logout(account_client)
    assert rv.status == '200 OK'


class Player(object):
    def __init__(self, username, password):
        self.client = app.test_client()
        rv = login(self.client, username, password)
        assert rv.status == '200 OK'


@pytest.mark.game
def test_seer_witch_hunter():
    players = [Player(f'test{i}', f'test{i}') for i in range(9)]
    host = players[0].client
    rv = host.post('/werewolf/setup', data=dict(
        victoryMode='KILL_GROUP',
        captainMode='WITH_CAPTAIN',
        witchMode='FIRST_NIGHT_ONLY',
        villager=3,
        normal_wolf=3,
        single_roles=['seer', 'witch', 'hunter']
    ), follow_redirects=True)
    assert rv.status == '200 OK'
