import sys
from pathlib import Path
import pytest
import json
from flask import request

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf.database import db, User, Game, Role
from werewolf.utils.enums import GameEnum
from werewolf.game_engine import GameEngine


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


class Player(Role):
    def __init__(self, client):
        self._client = client

    def get(self, *args, **kwargs):
        return self._client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self._client.post(*args, **kwargs)

    def use_skill(self, skill):
        return self._client.get('werewolf/api/' + skill)

    def check_cannot_use(self, skill):
        assert self.use_skill(skill).get_json()['msg'] != 'OK'


def prepare_player(app, username, password, nickname):  # noqa
    client = next(logged_client(app))
    register(client, username, password, nickname)
    login(client, username, password)
    return Player(client)


player_cnt = 0


def get_players(app, num):  # noqa
    global player_cnt
    players = []
    for _ in range(num):
        player_cnt += 1
        players.append(prepare_player(app, f'test{player_cnt}', f'test{player_cnt}', f'test{player_cnt}'))
    return players


def test_seer_witch_hunter(app):  # noqa
    players = get_players(app, 6)
    for p in players:
        assert logout(p).status_code == 200


def test_seer_wolf_villager(app):  # noqa
    # START test_seer_wolf_villager
    players = get_players(app, 6)
    # All players logged in, OK
    host = players[0]
    rv = host.post('/werewolf/setup', data=dict(
        victoryMode='kill_group',
        captainMode='with_captain',
        witchMode='first_night_only',
        villager=3,
        normal_wolf=2,
        single_roles=['seer']
    ))
    join_url = rv.location
    gid = int(join_url.split('=')[-1])
    print(f'New game established, gid={gid}')
    for p in players:
        assert p.get(join_url, follow_redirects=True).status_code == 200
    # All players joined the game, OK!
    for i, p in enumerate(players):
        rv = p.get(f'werewolf/api/sit?position={i+1}')
        assert rv.status_code == 200
        assert rv.get_json()['msg'] == 'OK'
        p.position = i + 1
    rv = host.get('werewolf/api/deal')
    assert rv.status_code == 200
    assert rv.get_json()['msg'] == 'OK'
    for p in players:
        rv = p.get('werewolf/api/get_game_info')
        assert rv.status_code == 200
        rv = rv.get_json()
        assert rv['msg'] == 'OK'
        assert rv['game']['status'][0] == GameEnum.GAME_STATUS_READY.name
        p.role_type = GameEnum[rv['role']['role_type'][0]]
        p.skills = [GameEnum[x[0]] for x in rv['role']['skills']]
    seer = None
    wolf = []
    villager = []
    for p in players:
        assert GameEnum.SKILL_VOTE in p.skills
        assert GameEnum.SKILL_CAPTAIN in p.skills
        if p.role_type is GameEnum.ROLE_TYPE_SEER:
            seer = p
            assert GameEnum.SKILL_DISCOVER in p.skills
        elif p.role_type is GameEnum.ROLE_TYPE_VILLAGER:
            villager.append(p)
        elif p.role_type is GameEnum.ROLE_TYPE_NORMAL_WOLF:
            wolf.append(p)
            assert GameEnum.SKILL_WOLF_KILL in p.skills
            assert GameEnum.SKILL_SUICIDE in p.skills
        else:
            raise TypeError(f'Wrong role type: {p.role_type}')
    assert seer is not None
    assert len(wolf) == 2
    assert len(villager) == 3
    # All roles ready

    seer.check_cannot_use('discover?target={}'.format(wolf[0].position))
    villager[0].check_cannot_use('vote?target=1')
    villager[0].check_cannot_use('elect?choice=yes')
    wolf[0].check_cannot_use('wolf_kill?target={}'.format(seer.position))
    wolf[0].check_cannot_use('suicide')

    game = Game.query.get(gid)
    assert game.status is GameEnum.GAME_STATUS_READY

    assert host.get('werewolf/api/next_step').status_code == 200
    ###############
    # FIRST DAY
    ###############
    game = Game.query.get(gid)
    assert game.status is GameEnum.GAME_STATUS_NIGHT
    # wolf turn
    assert GameEngine._current_step(game) is GameEnum.TAG_ATTACKABLE_WOLF
    seer.check_cannot_use('discover?target={}'.format(wolf[0].position))
    villager[0].check_cannot_use('vote?target=1')
    villager[0].check_cannot_use('elect?choice=yes')
    assert wolf[0].use_skill('wolf_kill?target={}'.format(villager[0].position)).get_json()['msg'] == 'OK'  # kill one villager
    # seer turn
    game = Game.query.get(gid)
    assert GameEngine._current_step(game) is GameEnum.ROLE_TYPE_SEER
    wolf[0].check_cannot_use('wolf_kill?target={}'.format(seer.position))
    wolf[1].check_cannot_use('wolf_kill?target={}'.format(villager[0].position))
    villager[0].check_cannot_use('vote?target=1')
    villager[0].check_cannot_use('elect?choice=yes')
    rv = seer.use_skill('discover?target={}'.format(wolf[0].position)).get_json()
    assert rv['msg'] == 'OK'
    assert '狼人' in rv['result']
    # turn day
    game = Game.query.get(gid)
    assert game.status is GameEnum.GAME_STATUS_DAY
    assert GameEngine._current_step(game) is GameEnum.TURN_STEP_ELECT
    seer.check_cannot_use('discover?target={}'.format(wolf[0].position))
    villager[0].check_cannot_use('vote?target=1')
    wolf[0].check_cannot_use('wolf_kill?target={}'.format(seer.position))

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
