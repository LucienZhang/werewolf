# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-10-05 16:03:18
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-09 13:14:10
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
