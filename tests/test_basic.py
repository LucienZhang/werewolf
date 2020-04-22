from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf.utils.enums import GameEnum
from werewolf.utils.json_utils import ExtendedJSONEncoder, json_hook


def test_enum_valid():
    a = GameEnum['VICTORY_MODE_UNKNOWN']
    b = GameEnum(100)
    c = GameEnum.VICTORY_MODE_UNKNOWN
    assert a is b
    assert b is c
    assert a is c
    assert a == b == c

    assert bool(a) is False
    assert bool(GameEnum(100)) is False
    assert bool(GameEnum.OK) is True
    assert bool(GameEnum(1)) is True

    assert isinstance(a, GameEnum)
    dumped_a = json.dumps(a, cls=ExtendedJSONEncoder)
    assert isinstance(dumped_a, str)
    assert dumped_a == '{"__GameEnum__": 100}'
    recovered_a = json.loads(dumped_a, object_hook=json_hook)
    assert isinstance(recovered_a, GameEnum)
    assert a is recovered_a
    assert a == recovered_a

    enum_l = [a, GameEnum(101)]
    dumped_l = json.dumps(enum_l, cls=ExtendedJSONEncoder)
    assert dumped_l == '[{"__GameEnum__": 100}, {"__GameEnum__": 101}]'
    recovered_l = json.loads(dumped_l, object_hook=json_hook)
    assert isinstance(recovered_l, list)
    assert len(recovered_l) == 2
    assert isinstance(recovered_l[0], GameEnum)
    assert recovered_l == enum_l
    assert recovered_l[0] is a
    assert recovered_l[1] == GameEnum(101)

    d = {a: 10, GameEnum(101): 20}
    assert b in d
    assert GameEnum(102) not in d

    assert isinstance(GameEnum.OK.digest(), dict)
    assert GameEnum.OK.digest() == {'code': 1, 'msg': 'OK'}
    # assert GameEnum.GAME_MESSAGE_DIE_IN_NIGHT.digest('1,2,3') == {'code': 707, 'msg': '昨晚，以下位置的玩家倒下了，不分先后： 1,2,3'}
    # assert GameEnum.GAME_MESSAGE_DIE_IN_NIGHT.digest('1,2,3', other='other info') == {'code': 707, 'msg': '昨晚，以下位置的玩家倒下了，不分先后： 1,2,3', 'other': 'other info'}
