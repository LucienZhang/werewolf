import json

from functools import singledispatch
from werewolf.utils.enums import GameEnum, EnumMember


@singledispatch
def convert(o):
    raise TypeError('not special type')


@convert.register(EnumMember)
def _(o):
    return {'__GameEnum__': o.name}


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return convert(obj)
        except TypeError:
            return super().default(obj)


def json_hook(d):
    if '__GameEnum__' in d:
        return GameEnum(d['__GameEnum__'])
    else:
        return d


def response(success, message=None, **kwargs):
    res = {'suc': success, 'msg': message}
    res.update(kwargs)
    return json.dumps(res)
