from pathlib import Path
import sys
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf.utils.enums import GameEnum, GameEnumMeta, EnumMember
from werewolf.utils.json_utils import ExtendedJSONEncoder, json_hook


def test_enum_unique():
    d = GameEnumMeta._enum_dict
    v = set()
    n = set()
    for key, member in d.items():
        assert member.value not in v
        assert member.name not in n
        assert key == member.name
        v.add(member.value)
        n.add(member.name)


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

    l = [a, GameEnum(1)]
    dumped_l = json.dumps(l, cls=ExtendedJSONEncoder)
    assert dumped_l == '[{"__GameEnum__": "GAME_STATUS_UNKNOWN"}, {"__GameEnum__": "GAME_STATUS_WAIT_TO_START"}]'
    recovered_l = json.loads(dumped_l, object_hook=json_hook)
    assert isinstance(recovered_l, list)
    assert len(recovered_l) == 2
    assert isinstance(recovered_l[0], EnumMember)
    assert recovered_l == l
    assert recovered_l[0] is a
    assert recovered_l[1] == GameEnum(1)

    d = {a: 10, GameEnum(1): 20}
    assert b in d
    assert GameEnum(2) not in d

    # test_enum_valid()
    # class A(object):
    #     def __init__(self, name, value, message):
    #         self.name = name
    #         self.value = value
    #         self.message = message
    #
    #     def __hash__(self):
    #         return hash(self.value)
    #     #
    #     # def __eq__(self, other):
    #     #     return self.value == other.value
    #     #
    #     def __str__(self):
    #         return self.name

    # from functools import singledispatch
    #
    #
    # @singledispatch
    # def convert(o):
    #     raise TypeError('not special type')
    #
    # @convert.register(dict)
    # def _(o):
    #     ret={}
    #     for k,v in o.items():
    #         ret[str(k)]=v
    #     return ret
    #
    # @convert.register(A)
    # def _(o):
    #     return {'__A__': o.name}
    #
    #
    # class Encoder(json.JSONEncoder):
    #     def default(self, obj):
    #         print('type:',type(obj))
    #         try:
    #             return convert(obj)
    #         except TypeError:
    #             return super().default(obj)
    #
    #
    # da = json.dumps({A('name', 1, 'message'):'val'}, cls=Encoder)
    # print(f'da:{da}')
    #
    #
    # def func(s):
    #     # print(s)
    #     return A(s['__A__'], 1, 'new message')
    #
    #
    # ra = json.loads(da, object_hook=func)
    # print(type(ra))
    # print(ra)
    # for k,v in ra.items():
    #     print(k.name,k.value,k.message,v)

    # aa=A('a',1,'ma')
    # bb=A('b',1,'mb')
    # l1=[aa,bb]
    # l2=l1.copy()
    # import random
    # random.shuffle(l2)
    # print(l1,l2)
