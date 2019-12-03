# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-10-05 16:03:18
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-09 13:14:10
import json

from functools import singledispatch
# from app.werewolf.role import Role
from enum import Enum
from flask import current_app
from werewolf.utils.enums import RoleType


@singledispatch
def convert(o):
    raise TypeError('not special type')


@convert.register(Enum)
def _(o):
    return o.name


# @convert.register(Turn)
# def _(o):
#     return o.__dict__


# @convert.register(Role)
# def _(o):
#     return o.__dict__

# @convert.register(datetime)
# def _(o):
#     return o.strftime('%b %d %Y %H:%M:%S')

# @convert.register(Decimal)
# def _(o):
#     return float(o)

# @convert.register(MyClass)
# def _(o):
#     return o.get_value()

def stringify_keys(d):
    """Convert a dict's keys to strings if they are not."""
    ans = {}
    for key in d.keys():
        # check inner dict
        if isinstance(d[key], dict):
            value = stringify_keys(d[key])
        else:
            value = d[key]

        # convert nonstring to string if needed
        if not isinstance(key, str):
            try:
                ans[str(key)] = value
            except Exception:
                try:
                    ans[repr(key)] = value
                except Exception:
                    raise
        else:
            ans[key] = value

            # delete old key
            # del d[key]
    return ans


class ExtendJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return convert(obj)
        except TypeError:
            return super().default(obj)


def JsonHook(cls=None):
    def hook(d):
        if cls == 'card_dict':
            obj = {}
            for k, v in d.items():
                obj[RoleType[k]] = v
            return obj
        elif cls is not None:
            obj = cls()
            obj.__dict__ = d
            return obj
        else:
            return d
    if cls is not None:
        return hook
    else:
        return None
