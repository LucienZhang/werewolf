from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf.utils.enums import GameEnum, GameEnumMeta, EnumMember
from werewolf.utils.json_utils import ExtendedJSONEncoder, json_hook


def test_enum_unique():
    d = GameEnumMeta._enums
    v = set()
    n = set()
    for e in d:
        assert e.value not in v
        assert e.name not in n
        v.add(e.value)
        n.add(e.name)


def test_enum_valid():
    a = GameEnum('GAME_STATUS_UNKNOWN')
    b = GameEnum(0)
    c = GameEnum.GAME_STATUS_UNKNOWN
    assert a is b
    assert b is c
    assert a is c
    assert a == b == c

    assert isinstance(a, EnumMember)
    dumped_a = json.dumps(a, cls=ExtendedJSONEncoder)
    assert isinstance(dumped_a, str)
    assert a.name == str(a)
    assert dumped_a == '{"__GameEnum__": "GAME_STATUS_UNKNOWN"}'
    recovered_a = json.loads(dumped_a, object_hook=json_hook)
    assert isinstance(recovered_a, EnumMember)
    assert a is b
    assert a == b

    enum_l = [a, GameEnum(1)]
    dumped_l = json.dumps(enum_l, cls=ExtendedJSONEncoder)
    assert dumped_l == '[{"__GameEnum__": "GAME_STATUS_UNKNOWN"}, {"__GameEnum__": "GAME_STATUS_WAIT_TO_START"}]'
    recovered_l = json.loads(dumped_l, object_hook=json_hook)
    assert isinstance(recovered_l, list)
    assert len(recovered_l) == 2
    assert isinstance(recovered_l[0], EnumMember)
    assert recovered_l == enum_l
    assert recovered_l[0] is a
    assert recovered_l[1] == GameEnum(1)

    d = {a: 10, GameEnum(1): 20}
    assert b in d
    assert GameEnum(2) not in d
