# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-10-04 15:43:49
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-09 13:11:33


class EnumMember(object):
    def __init__(self, name, value, message):
        self.name = name
        self.value = value
        self.message = message

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __str__(self):
        return self.name


# todo: add messages!
class GameEnumMeta(type):
    _enum_dict = {
        # 0
        'GAME_STATUS_UNKNOWN': EnumMember('GAME_STATUS_UNKNOWN', 0, ''),
        'GAME_STATUS_WAIT_TO_START': EnumMember('GAME_STATUS_WAIT_TO_START', 1, ''),
        'GAME_STATUS_DAY': EnumMember('GAME_STATUS_DAY', 2, ''),
        'GAME_STATUS_NIGHT': EnumMember('GAME_STATUS_NIGHT', 3, ''),
        'GAME_STATUS_ELECTING': EnumMember('GAME_STATUS_ELECTING', 4, ''),
        'GAME_STATUS_VOTING': EnumMember('GAME_STATUS_VOTING', 5, ''),
        'GAME_STATUS_VOTING_FOR_CAPTAIN': EnumMember('GAME_STATUS_VOTING_FOR_CAPTAIN', 6, ''),
        'GAME_STATUS_WAITING': EnumMember('GAME_STATUS_WAITING', 7, ''),  # TODO: what is this for?????
        # 100
        'VICTORY_MODE_UNKNOWN': EnumMember('VICTORY_MODE_UNKNOWN', 100, ''),
        'VICTORY_MODE_KILL_GROUP': EnumMember('VICTORY_MODE_KILL_GROUP', 101, ''),
        'VICTORY_MODE_KILL_ALL': EnumMember('VICTORY_MODE_KILL_ALL', 102, ''),
        # 200
        'CAPTAIN_MODE_UNKNOWN': EnumMember('CAPTAIN_MODE_UNKNOWN', 200, ''),
        'CAPTAIN_MODE_WITH_CAPTAIN': EnumMember('CAPTAIN_MODE_WITH_CAPTAIN', 201, ''),
        'CAPTAIN_MODE_WITHOUT_CAPTAIN': EnumMember('CAPTAIN_MODE_WITHOUT_CAPTAIN', 202, ''),
        # 300
        'WITCH_MODE_UNKNOWN': EnumMember('WITCH_MODE_UNKNOWN', 300, ''),
        'WITCH_MODE_CAN_SAVE_SELF': EnumMember('WITCH_MODE_CAN_SAVE_SELF', 301, ''),
        'WITCH_MODE_FIRST_NIGHT_ONLY': EnumMember('WITCH_MODE_FIRST_NIGHT_ONLY', 302, ''),
        'WITCH_MODE_CANNOT_SAVE_SELF': EnumMember('WITCH_MODE_CANNOT_SAVE_SELF', 303, ''),
        # 400
        'ROLE_TYPE_UNKNOWN': EnumMember('ROLE_TYPE_UNKNOWN', 400, ''),
        'ROLE_TYPE_SEER': EnumMember('ROLE_TYPE_SEER', 401, ''),
        'ROLE_TYPE_HUNTER': EnumMember('ROLE_TYPE_HUNTER', 402, ''),
        'ROLE_TYPE_CUPID': EnumMember('ROLE_TYPE_CUPID', 403, ''),
        'ROLE_TYPE_WITCH': EnumMember('ROLE_TYPE_WITCH', 404, ''),
        'ROLE_TYPE_LITTLE_GIRL': EnumMember('ROLE_TYPE_LITTLE_GIRL', 405, ''),
        'ROLE_TYPE_THIEF': EnumMember('ROLE_TYPE_THIEF', 406, ''),
        'ROLE_TYPE_VILLAGER': EnumMember('ROLE_TYPE_VILLAGER', 407, ''),
        'ROLE_TYPE_NORMAL_WOLF': EnumMember('ROLE_TYPE_NORMAL_WOLF', 408, ''),
        'ROLE_TYPE_IDIOT': EnumMember('ROLE_TYPE_IDIOT', 409, ''),
        'ROLE_TYPE_ANCIENT': EnumMember('ROLE_TYPE_ANCIENT', 410, ''),
        'ROLE_TYPE_SCAPEGOAT': EnumMember('ROLE_TYPE_SCAPEGOAT', 411, ''),
        'ROLE_TYPE_SAVIOR': EnumMember('ROLE_TYPE_SAVIOR', 412, ''),
        'ROLE_TYPE_PIPER': EnumMember('ROLE_TYPE_PIPER', 413, ''),
        'ROLE_TYPE_WHITE_WOLF': EnumMember('ROLE_TYPE_WHITE_WOLF', 414, ''),
        'ROLE_TYPE_RAVEN': EnumMember('ROLE_TYPE_RAVEN', 415, ''),
        'ROLE_TYPE_PYROMANIAC': EnumMember('ROLE_TYPE_PYROMANIAC', 416, ''),
        'ROLE_TYPE_TWO_SISTERS': EnumMember('ROLE_TYPE_TWO_SISTERS', 417, ''),
        'ROLE_TYPE_THREE_BROTHERS': EnumMember('ROLE_TYPE_THREE_BROTHERS', 418, ''),
        'ROLE_TYPE_ANGEL': EnumMember('ROLE_TYPE_ANGEL', 419, ''),
        'ROLE_TYPE_ALL_WOLF': EnumMember('ROLE_TYPE_ALL_WOLF', 420, ''),
        # 500
        'GROUP_TYPE_UNKNOWN': EnumMember('GROUP_TYPE_UNKNOWN', 500, ''),
        'GROUP_TYPE_WOLVES': EnumMember('GROUP_TYPE_WOLVES', 501, ''),
        'GROUP_TYPE_GODS': EnumMember('GROUP_TYPE_GODS', 502, ''),
        'GROUP_TYPE_VILLAGERS': EnumMember('GROUP_TYPE_VILLAGERS', 503, ''),
        'GROUP_TYPE_THIRD_PARTY': EnumMember('GROUP_TYPE_THIRD_PARTY', 504, ''),
        # 600
        'TURN_STEP_UNKNOWN': EnumMember('TURN_STEP_UNKNOWN', 600, ''),
        'TURN_STEP_CHECK_VICTORY': EnumMember('TURN_STEP_CHECK_VICTORY', 601, ''),
        'TURN_STEP_TURN_NIGHT': EnumMember('TURN_STEP_TURN_NIGHT', 602, ''),
        'TURN_STEP_TURN_DAY': EnumMember('TURN_STEP_TURN_DAY', 603, ''),
        'TURN_STEP_ELECT': EnumMember('TURN_STEP_ELECT', 604, ''),
        'TURN_STEP_VOTE_FOR_CAPTAIN': EnumMember('TURN_STEP_VOTE_FOR_CAPTAIN', 605, ''),
        'TURN_STEP_VOTE': EnumMember('TURN_STEP_VOTE', 606, ''),
        'TURN_STEP_TALK': EnumMember('TURN_STEP_TALK', 607, ''),
        'TURN_STEP_ANNOUNCE_AND_TALK': EnumMember('TURN_STEP_ANNOUNCE_AND_TALK', 608, ''),

        # 700
        'GAME_MESSAGE_GAME_NOT_EXIST': EnumMember('GAME_MESSAGE_GAME_NOT_EXIST', 700, '房间不存在'),
        'GAME_MESSAGE_GAME_FULL': EnumMember('GAME_MESSAGE_GAME_FULL', 701, '房间已满'),
        'GAME_MESSAGE_ALREADY_IN': EnumMember('GAME_MESSAGE_ALREADY_IN', 702, '你已在游戏中'),
        'GAME_MESSAGE_ROLE_NOT_EXIST': EnumMember('GAME_MESSAGE_ROLE_NOT_EXIST', 703, '角色不存在'),
        'GAME_MESSAGE_NOT_IN_GAME': EnumMember('GAME_MESSAGE_NOT_IN_GAME', 704, '你不在游戏中'),
        'GAME_MESSAGE_CANNOT_START': EnumMember('GAME_MESSAGE_CANNOT_START', 705, '玩家不足，无法开始'),
        'GAME_MESSAGE_UNKNOWN_OP': EnumMember('GAME_MESSAGE_UNKNOWN_OP', 706, '未知命令'),
        'GAME_MESSAGE_DIE_IN_NIGHT': EnumMember('GAME_MESSAGE_DIE_IN_NIGHT', 707, '昨晚，以下位置的玩家倒下了，不分先后： {}'),

        'PLACE_HOLDER': EnumMember('PLACE_HOLDER', 9999, '')
    }

    @staticmethod
    def _item(k):
        if isinstance(k, str):
            return GameEnumMeta._enum_dict[k]
        elif isinstance(k, int):
            for ins in GameEnumMeta._enum_dict.values():
                if ins.value == k:
                    return ins
            else:
                raise KeyError(f'No enum has value of {k}')
        else:
            raise KeyError(f'Expect int or str, but received {type(k)}')

    def __getattr__(self, item):
        if item == 'item':
            return GameEnumMeta._item
        elif item in GameEnumMeta._enum_dict:
            return GameEnumMeta._enum_dict[item]
        else:
            return super().__getattribute__(item)


class GameEnum(metaclass=GameEnumMeta):
    def __new__(cls, *args, **kwargs):
        assert len(args) == 1 and len(kwargs) == 0
        k = args[0]
        return GameEnum.item(k)

#
#
# class VictoryMode(Enum):
#     UNKNOWN = 100
#     KILL_GROUP = auto()  # 屠边
#     KILL_ALL = auto()  # 屠城
#
#     def __str__(self):
#         return self.name
#
#
# class CaptainMode(Enum):
#     UNKNOWN = 200
#     WITH_CAPTAIN = auto()  # 有警长
#     WITHOUT_CAPTAIN = auto()  # 没有警长
#
#     def __str__(self):
#         return self.name
#
#
# class WitchMode(Enum):
#     UNKNOWN = 300
#     CAN_SAVE_SELF = auto()  # 全程可以自救
#     FIRST_NIGHT_ONLY = auto()  # 仅首夜可以自救
#     CANNOT_SAVE_SELF = auto()  # 全程不可自救
#
#     def __str__(self):
#         return self.name
#
#
