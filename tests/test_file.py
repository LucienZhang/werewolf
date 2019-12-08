import pytest
import sys, inspect

sys.path.append('..')
from werewolf.utils import enums
from werewolf.utils.enums import *
from werewolf.utils.enums import GameEnumMeta


def test_1():
    # print(sys.modules)
    clsmembers = inspect.getmembers(sys.modules['werewolf.utils.enums'], inspect.isclass)
    values = set()
    for name, obj in clsmembers:
        if name in ['Enum', 'auto']:
            continue
        for e in obj:
            assert e.value not in values
            values.add(e.value)


def test_2():
    d = GameEnumMeta.enum_dict
    s = set()
    for i, _ in d.values():
        assert i not in s
        s.add(i)


def test_3():
    a = GameEnum('ROLE_TYPE_WHITE_WOLF')
    b = GameEnum(414)
    # print(GameEnumMeta.__dict__)
    c = GameEnum.ROLE_TYPE_WHITE_WOLF
    assert a is b
    assert b is c
    assert a == b == c
