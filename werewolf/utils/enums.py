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
    _enums = [
        # negative positions
        EnumMember('TARGET_NOT_ACTED', -2, ''),
        EnumMember('TARGET_NO_ONE', -1, ''),

        # 0
        EnumMember('GAME_STATUS_UNKNOWN', 0, ''),
        EnumMember('GAME_STATUS_WAIT_TO_START', 1, '等待开始'),
        EnumMember('GAME_STATUS_READY', 2, '游戏已准备好'),
        EnumMember('GAME_STATUS_DAY', 3, '白天'),
        EnumMember('GAME_STATUS_NIGHT', 4, '夜晚'),

        # 100
        EnumMember('VICTORY_MODE_UNKNOWN', 100, ''),
        EnumMember('VICTORY_MODE_KILL_GROUP', 101, '屠边'),
        EnumMember('VICTORY_MODE_KILL_ALL', 102, '屠城'),
        # 200
        EnumMember('CAPTAIN_MODE_UNKNOWN', 200, ''),
        EnumMember('CAPTAIN_MODE_WITH_CAPTAIN', 201, '有警长'),
        EnumMember('CAPTAIN_MODE_WITHOUT_CAPTAIN', 202, '没有警长'),
        # 300
        EnumMember('WITCH_MODE_UNKNOWN', 300, ''),
        EnumMember('WITCH_MODE_CAN_SAVE_SELF', 301, '全程可以自救'),
        EnumMember('WITCH_MODE_FIRST_NIGHT_ONLY', 302, '仅首夜可以自救'),
        EnumMember('WITCH_MODE_CANNOT_SAVE_SELF', 303, '全程不可自救'),
        # 400
        EnumMember('ROLE_TYPE_UNKNOWN', 400, '没有角色'),
        EnumMember('ROLE_TYPE_SEER', 401, '预言家'),
        EnumMember('ROLE_TYPE_HUNTER', 402, '猎人'),
        EnumMember('ROLE_TYPE_CUPID', 403, '丘比特'),
        EnumMember('ROLE_TYPE_WITCH', 404, '女巫'),
        EnumMember('ROLE_TYPE_LITTLE_GIRL', 405, '小女孩'),
        EnumMember('ROLE_TYPE_THIEF', 406, '盗贼'),
        EnumMember('ROLE_TYPE_VILLAGER', 407, '普通村民'),
        EnumMember('ROLE_TYPE_NORMAL_WOLF', 408, '普通狼人'),
        EnumMember('ROLE_TYPE_IDIOT', 409, '白痴'),
        EnumMember('ROLE_TYPE_ANCIENT', 410, '长老'),
        EnumMember('ROLE_TYPE_SCAPEGOAT', 411, '替罪羊'),
        EnumMember('ROLE_TYPE_SAVIOR', 412, '守卫'),
        EnumMember('ROLE_TYPE_PIPER', 413, '吹笛者'),
        EnumMember('ROLE_TYPE_WHITE_WOLF', 414, '白狼王'),
        EnumMember('ROLE_TYPE_RAVEN', 415, '乌鸦'),
        EnumMember('ROLE_TYPE_PYROMANIAC', 416, '火狼'),
        EnumMember('ROLE_TYPE_TWO_SISTERS', 417, '两姐妹'),
        EnumMember('ROLE_TYPE_THREE_BROTHERS', 418, '三兄弟'),
        EnumMember('ROLE_TYPE_ANGEL', 419, '天使'),
        EnumMember('ROLE_TYPE_ALL_WOLF', 420, '全部狼人'),
        # 500
        EnumMember('GROUP_TYPE_UNKNOWN', 500, '未知阵营'),
        EnumMember('GROUP_TYPE_WOLVES', 501, '狼人阵营'),
        EnumMember('GROUP_TYPE_GODS', 502, '神阵营'),
        EnumMember('GROUP_TYPE_VILLAGERS', 503, '民阵营'),
        EnumMember('GROUP_TYPE_THIRD_PARTY', 504, '第三方势力'),
        # 600
        EnumMember('TURN_STEP_UNKNOWN', 600, ''),
        EnumMember('TURN_STEP_DEAL', 601, '发牌'),
        EnumMember('TURN_STEP_TURN_NIGHT', 602, ''),
        EnumMember('TURN_STEP_TURN_DAY', 603, ''),
        EnumMember('TURN_STEP_ELECT', 604, ''),
        EnumMember('TURN_STEP_VOTE_FOR_CAPTAIN', 605, ''),
        EnumMember('TURN_STEP_VOTE', 606, ''),
        EnumMember('TURN_STEP_TALK', 607, ''),
        EnumMember('TURN_STEP_ANNOUNCE', 608, ''),
        # EnumMember('TURN_STEP_WAITING_FOR_SHOOT', 609, ''),
        EnumMember('TURN_STEP_PK', 610, ''),
        EnumMember('TURN_STEP_CAPTAIN_PK', 611, ''),
        EnumMember('TURN_STEP_LAST_WORDS', 612, ''),

        # 700
        EnumMember('GAME_MESSAGE_GAME_NOT_EXIST', 700, '房间不存在'),
        EnumMember('GAME_MESSAGE_GAME_FULL', 701, '房间已满'),
        EnumMember('GAME_MESSAGE_ALREADY_IN', 702, '你已在游戏中'),
        EnumMember('GAME_MESSAGE_ROLE_NOT_EXIST', 703, '角色不存在'),
        EnumMember('GAME_MESSAGE_NOT_IN_GAME', 704, '你不在游戏中'),
        EnumMember('GAME_MESSAGE_CANNOT_START', 705, '玩家不足，无法开始'),
        EnumMember('GAME_MESSAGE_UNKNOWN_OP', 706, '未知命令'),
        EnumMember('GAME_MESSAGE_DIE_IN_NIGHT', 707, '昨晚，以下位置的玩家倒下了，不分先后： {}'),
        EnumMember('GAME_MESSAGE_ALREADY_STARTED', 708, '游戏已经开始了'),
        EnumMember('GAME_MESSAGE_POSITION_OCCUPIED', 709, '那个位置已经有人了'),
        EnumMember('GAME_MESSAGE_CANNOT_ACT', 710, '当前无法操作'),

        # 800
        EnumMember('SKILL_VOTE', 800, '投票'),
        EnumMember('SKILL_WOLF_KILL', 801, '狼刀'),
        EnumMember('SKILL_DISCOVER', 802, '查验'),
        EnumMember('SKILL_WITCH', 803, '用药'),
        EnumMember('SKILL_GUARD', 804, '守护'),
        EnumMember('SKILL_SHOOT', 805, '开枪'),
        EnumMember('SKILL_EXPLODE', 806, '自爆'),
        EnumMember('SKILL_TOXIC', 807, '毒杀'),

        # 900
        EnumMember('TAG_ELECT', 900, '上警'),
        EnumMember('TAG_NOT_ELECT', 901, '不上警'),
        EnumMember('TAG_GIVE_UP_ELECT', 902, '退水'),


        EnumMember('PLACE_HOLDER', 9999, '')
    ]

    def __new__(mcs, name, bases, attrs):
        enum_dict = {}
        attrs['_enum_dict'] = enum_dict
        for e in GameEnumMeta._enums:
            name, value = e.name, e.value
            enum_dict[value] = e
            attrs[name] = e
        return super().__new__(mcs, name, bases, attrs)


class GameEnum(metaclass=GameEnumMeta):
    def __setattr__(self, key, value):
        raise Exception('Cannot change the attributes of this class!')

    def __new__(cls, key):
        if isinstance(key, str):
            return super().__getattribute__(cls, key)
        elif isinstance(key, int):
            return cls._enum_dict[key]
        else:
            raise TypeError(
                f'Expecting string or int, got {key} with format {type(key)}')
