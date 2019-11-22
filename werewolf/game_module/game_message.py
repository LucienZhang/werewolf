# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-10-06 22:08:14
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 15:45:01

from enum import Enum
from werewolf.utils.enums import *


class GameMessage(object):
    message_dict = {
        'GAME_NOT_EXIST': '房间不存在',
        'GAME_FULL': '房间已满',
        'ALREADY_IN': '你已在游戏中',
        'ROLE_NOT_EXIST': '角色不存在',
        'PLACE_HOLDER': '占位符'
    }

    message_dict[VictoryMode.KILL_ALL] = '屠城'
    message_dict[VictoryMode.KILL_GROUP] = '屠边'
    message_dict[CaptainMode.WITH_CAPTAIN] = '有警长'
    message_dict[CaptainMode.WITHOUT_CAPTAIN] = '没有警长'
    message_dict[WitchMode.CAN_SAVE_SELF] = '全程可以自救'
    message_dict[WitchMode.FIRST_NIGHT_ONLY] = '仅首夜可以自救'
    message_dict[WitchMode.CANNOT_SAVE_SELF] = '全程不可自救'

    message_dict[RoleType.UNKNOWN] = '没有角色'
    message_dict[RoleType.SEER] = '预言家'
    message_dict[RoleType.HUNTER] = '猎人'
    message_dict[RoleType.CUPID] = '丘比特'
    message_dict[RoleType.WITCH] = '女巫'
    message_dict[RoleType.LITTLE_GIRL] = '小女孩'
    message_dict[RoleType.THIEF] = '盗贼'
    message_dict[RoleType.VILLAGER] = '普通村民'
    message_dict[RoleType.NORMAL_WOLF] = '普通狼人'
    message_dict[RoleType.IDIOT] = '白痴'
    message_dict[RoleType.ANCIENT] = '长老'
    message_dict[RoleType.SCAPEGOAT] = '替罪羊'
    message_dict[RoleType.SAVIOR] = '守卫'
    message_dict[RoleType.PIPER] = '吹笛者'
    message_dict[RoleType.WHITE_WOLF] = '白狼王'
    message_dict[RoleType.RAVEN] = '乌鸦'
    message_dict[RoleType.PYROMANIAC] = '火狼'
    message_dict[RoleType.TWO_SISTERS] = '两姐妹'
    message_dict[RoleType.THREE_BROTHERS] = '三兄弟'
    message_dict[RoleType.ANGEL] = '天使'
    message_dict[RoleType.ALL_WOLF] = '狼人'

    def __init__(self, key, arg=None):
        assert(key in GameMessage.message_dict)
        self.key = key
        self.arg = arg

    def parse(self):
        if self.arg is None:
            return GameMessage.message_dict[self.key]
        else:
            return GameMessage.message_dict[self.key].format(*self.arg)
