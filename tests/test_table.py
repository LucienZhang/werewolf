import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import pytest
import json
import collections
from sqlalchemy.exc import IntegrityError

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf.database import db, User, Game, Role
from werewolf.utils.enums import GameEnum


@pytest.mark.usefixtures('app')
def test_user_table():
    user = User(username='username-table', password='password', login_token='login_token', nickname='nickname', avatar=0, gid=-1)
    db.session.add(user)
    db.session.commit()
    assert isinstance(user.uid, int)
    new_user = User.query.get(user.uid)
    assert new_user.username == 'username-table'
    assert new_user.password == 'password'
    assert new_user.login_token == 'login_token'
    assert new_user.nickname == 'nickname'
    assert new_user.avatar == 0
    assert new_user.gid == -1

    # duplicated name
    user2 = User(username='username-table', password='password', login_token='login_token', nickname='nickname', avatar=0, gid=-1)
    raised = False
    try:
        db.session.add(user2)
        db.session.commit()
    except IntegrityError:
        raised = True
        db.session.rollback()
    assert raised


@pytest.mark.usefixtures('app')
def test_game_table():
    game = Game(host_uid=1,
                victory_mode=GameEnum.VICTORY_MODE_KILL_ALL,
                captain_mode=GameEnum.CAPTAIN_MODE_UNKNOWN,
                witch_mode=GameEnum.WITCH_MODE_CAN_SAVE_SELF,
                wolf_mode=GameEnum.WOLF_MODE_ALL,
                cards=[],
                status=GameEnum.GAME_STATUS_WAIT_TO_START,
                end_time=datetime.utcnow() + timedelta(days=1),
                days=0,
                now_index=-1,
                steps=[],
                step_cnt=0,
                history={},
                captain_pos=-1,
                players=[],
                )
    db.session.add(game)
    db.session.commit()
    assert game.gid is not None
    assert game.updated_on is not None

    timestamp1 = game.updated_on
    time.sleep(0.01)
    affected_cnt = db.session.query(Game).filter(Game.gid == game.gid, Game.updated_on == str(timestamp1)).update({'days': 1})
    db.session.commit()
    assert affected_cnt == 1
    game2 = Game.query.get(game.gid)
    assert game2.victory_mode is GameEnum.VICTORY_MODE_KILL_ALL
    assert game2.cards == []
    assert game2.history == {}
    timestamp2 = game2.updated_on
    assert timestamp1 != timestamp2
    affected_cnt = db.session.query(Game).filter(Game.gid == game.gid, Game.updated_on == str(timestamp1)).update({'days': 1})
    db.session.commit()
    assert affected_cnt == 0
    assert Game.query.get(game.gid).updated_on == timestamp2
    time.sleep(0.01)
    affected_cnt = db.session.query(Game).filter(Game.gid == game.gid, Game.updated_on == str(timestamp2)).update({'days': 1})
    db.session.commit()
    assert affected_cnt == 1
    assert Game.query.get(game.gid).updated_on != timestamp2

    game3 = Game.query.get(game.gid)
    timestamp3 = game3.updated_on
    assert datetime.utcnow() < game3.end_time
    affected_cnt = db.session.query(Game).filter(Game.gid == game3.gid, Game.updated_on == str(timestamp3)).update({'end_time': datetime.utcnow() + timedelta(seconds=1)})
    db.session.commit()
    assert affected_cnt == 1
    time.sleep(1.1)
    game4 = Game.query.get(game3.gid)
    db.session.commit()
    assert datetime.utcnow() > game4.end_time


@pytest.mark.usefixtures('app')
def test_role_table():
    role1 = Role(uid=101, nickname='nickname', avatar=1, gid=101)
    role1.reset()
    role1.group_type = GameEnum.GROUP_TYPE_GODS
    role2 = Role(uid=102, nickname='nickname', avatar=1, gid=101)
    role2.reset()
    role2.group_type = GameEnum.GROUP_TYPE_WOLVES
    role3 = Role(uid=103, nickname='nickname', avatar=1, gid=101)
    role3.reset()
    role3.group_type = GameEnum.GROUP_TYPE_WOLVES
    db.session.add(role1)
    db.session.add(role2)
    db.session.add(role3)
    db.session.commit()
    roles = Role.query.filter(Role.gid == 101).all()
    assert len(roles) == 3
    assert isinstance(roles[0], Role)
    from sqlalchemy import func
    groups = db.session.query(Role.group_type, func.count(Role.group_type)).filter(Role.gid == 101).group_by(Role.group_type).all()
    assert len(groups) == 2
    assert isinstance(groups, list)
    for g, cnt in groups:
        assert g in [GameEnum.GROUP_TYPE_GODS, GameEnum.GROUP_TYPE_WOLVES]
        if g is GameEnum.GROUP_TYPE_GODS:
            assert cnt == 1
        elif g is GameEnum.GROUP_TYPE_WOLVES:
            assert cnt == 2
    groups = Role.query.with_entities(Role.group_type, func.count(Role.group_type)).filter(Role.gid == 101, Role.alive == int(True)).group_by(Role.group_type).all()
    assert len(groups) == 2
    assert isinstance(groups, list)
    for g, cnt in groups:
        assert g in [GameEnum.GROUP_TYPE_GODS, GameEnum.GROUP_TYPE_WOLVES]
        if g is GameEnum.GROUP_TYPE_GODS:
            assert cnt == 1
        elif g is GameEnum.GROUP_TYPE_WOLVES:
            assert cnt == 2
    players = Role.query.with_entities(Role.position, Role.group_type).filter(Role.gid == 101, Role.alive == int(True)).all()
    groups = collections.defaultdict(int)
    for p, g in players:
        groups[g] += 1
    assert GameEnum.GROUP_TYPE_GODS in groups
    assert groups[GameEnum.GROUP_TYPE_GODS] == 1
    assert GameEnum.GROUP_TYPE_WOLVES in groups
    assert groups[GameEnum.GROUP_TYPE_WOLVES] == 2

    player_cnt = db.session.query(db.func.count(Role.uid)).filter(Role.gid == 101, Role.alive == int(True), Role.group_type == GameEnum.GROUP_TYPE_WOLVES).scalar()
    assert isinstance(player_cnt, int)
    assert player_cnt == 2
