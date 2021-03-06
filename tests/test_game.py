import sys
from pathlib import Path
import pytest
import json
from flask import request

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf.database import db


def login(client, username, password):
    return client.post('/werewolf/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def logout(client):
    return client.get('/werewolf/logout', follow_redirects=True)


def register(client, username, password, nickname):
    return client.post('/werewolf/register', data=dict(
        username=username,
        password=password,
        nickname=nickname
    ), follow_redirects=True)


@pytest.mark.login
def test_register_login_logout(app):  # noqa
    client = app.test_client()
    assert register(client, 'username-login', 'password', 'nickname').status_code == 200
    assert login(client, 'username-login', 'password').status_code == 200
    rv = logout(client)
    assert rv.status_code == 200
    assert rv.is_json
    assert rv.get_json() == {'code': 9999, 'msg': 'OK'}


def logged_client(app):  # noqa
    with app.test_client() as c:
        yield c


def prepare_player(app, username, password, nickname):  # noqa
    client = next(logged_client(app))
    register(client, username, password, nickname)
    login(client, username, password)
    return client


def get_players(app, num):  # noqa
    players = []
    for i in range(num):
        players.append(prepare_player(app, f'test{i}', f'test{i}', f'test{i}'))
    return players


def test_seer_witch_hunter(app):  # noqa
    players = get_players(app, 6)
    for p in players:
        assert logout(p).status_code == 200

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
