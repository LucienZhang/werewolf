import pytest
import sys, inspect

sys.path.append('..')
from werewolf.utils import enums
from werewolf.utils.enums import *


def test_1():
    # print(sys.modules)
    clsmembers = inspect.getmembers(sys.modules['werewolf.utils.enums'], inspect.isclass)
    values=set()
    for name, obj in clsmembers:
        if name in ['Enum', 'auto']:
            continue
        for e in obj:
            assert e.value not in values
            values.add(e.value)


