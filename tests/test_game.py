import sys
from pathlib import Path
import pytest
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))
from tests.env import init_table, app, db

# @pytest.fixture(scope='function')
# def account_client():
#     with app.test_client() as account_client:
#         yield account_client


def login(client, username, password):
    return client.post('/werewolf/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def logout(client):
    return client.get('/werewolf/logout', follow_redirects=True)


def register(client, username, password, nickname):
    return client.post('/werewolf/login', data=dict(
        username=username,
        password=password,
        nickname=nickname
    ), follow_redirects=True)


@pytest.mark.login
@pytest.mark.usefixtures('init_table')
def test_register_login_logout():
    client = app.test_client()
    assert register(client, 'username', 'password', 'nickname').status_code == 200
    assert login(client, 'username', 'password').status_code == 200
    assert logout(client).status_code == 200


# class Player(object):
#     def __init__(self, username, password):
#         self.client = app.test_client()
#         rv = login(self.client, username, password)
#         assert rv.status == '200 OK'


# @pytest.mark.game
# def test_seer_witch_hunter():
#     print('START to test the seer witch hunter')
#     players = [Player(f'test{i}', f'test{i}').client for i in range(9)]
#     print('All players logged in, OK')
#     host = players[0]
#     rv = host.post('/werewolf/setup', data=dict(
#         victoryMode='KILL_GROUP',
#         captainMode='WITH_CAPTAIN',
#         witchMode='FIRST_NIGHT_ONLY',
#         villager=3,
#         normal_wolf=3,
#         single_roles=['seer', 'witch', 'hunter']
#     ), follow_redirects=True)
#     assert rv.status == '200 OK'
#     print('Game established, OK!')
#     rv = host.get('werewolf/test?cmd=get_info')
#     assert rv.status_code == 200
#     info = rv.data
#     info = json.loads(info)
#     gid = info['user']['gid']
#     print(f'New game gid={gid}')

#     for player in players[1:]:
#         rv = player.get(f'/werewolf/join?gid={gid}', follow_redirects=True)
#         assert rv.status == '200 OK'
#     print('All players joined the game, OK!')
#     rv = host.get('werewolf/action?op=start')
#     assert rv.status_code == 200
#     print('Game started, OK!')
#     normal_wolf = []
#     villager = []
#     seer = None
#     witch = None
#     hunter = None
#     for player in players:
#         rv = player.get('werewolf/test?cmd=get_info')
#         assert rv.status_code == 200
#         info = rv.data
#         info = json.loads(info)
#         role_type = info['role']['role_type']
#         if role_type == 'ROLE_TYPE_SEER':
#             print('Seer got, OK!')
#             seer = player
#             continue
#         elif role_type == 'ROLE_TYPE_WITCH':
#             print('Witch got, OK!')
#             witch = player
#             continue
#         elif role_type == 'ROLE_TYPE_HUNTER':
#             print('Hunter got, OK!')
#             hunter = player
#             continue
#         elif role_type == 'ROLE_TYPE_NORMAL_WOLF':
#             print('Normal wolf got, OK!')
#             normal_wolf.append(player)
#             continue
#         elif role_type == 'ROLE_TYPE_VILLAGER':
#             print('Villager got, OK!')
#             villager.append(player)
#             continue
#     assert seer and witch and hunter and len(normal_wolf) == 3 and len(villager) == 3
