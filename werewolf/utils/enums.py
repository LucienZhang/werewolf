# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-10-04 15:43:49
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-09 13:11:33

from enum import Enum, auto


class GameStatus(Enum):
    UNKNOWN = 0
    WAIT_TO_START = auto()
    DAY = auto()
    NIGHT = auto()
    ELECTING = auto()
    VOTING = auto()
    VOTING_FOR_CAPTAIN = auto()
    WAITING = auto()  # TODO: what is this for?????

    def __str__(self):
        return self.name


class VictoryMode(Enum):
    UNKNOWN = 0
    KILL_GROUP = auto()  # 屠边
    KILL_ALL = auto()  # 屠城

    def __str__(self):
        return self.name


class CaptainMode(Enum):
    UNKNOWN = 0
    WITH_CAPTAIN = auto()  # 有警长
    WITHOUT_CAPTAIN = auto()  # 没有警长

    def __str__(self):
        return self.name


class WitchMode(Enum):
    UNKNOWN = 0
    CAN_SAVE_SELF = auto()  # 全程可以自救
    FIRST_NIGHT_ONLY = auto()  # 仅首夜可以自救
    CANNOT_SAVE_SELF = auto()  # 全程不可自救

    def __str__(self):
        return self.name


class RoleType(Enum):
    UNKNOWN = 0
    SEER = auto()
    HUNTER = auto()
    CUPID = auto()
    WITCH = auto()
    LITTLE_GIRL = auto()
    THIEF = auto()
    VILLAGER = auto()
    NORMAL_WOLF = auto()
    IDIOT = auto()
    ANCIENT = auto()
    SCAPEGOAT = auto()
    SAVIOR = auto()
    PIPER = auto()
    WHITE_WOLF = auto()
    RAVEN = auto()
    PYROMANIAC = auto()
    TWO_SISTERS = auto()
    THREE_BROTHERS = auto()
    ANGEL = auto()
    ALL_WOLF = auto()

    def __str__(self):
        return self.name


class GroupType(Enum):
    UNKNOWN = 0
    WOLVES = auto()
    GODS = auto()
    VILLAGERS = auto()
    THIRD_PARTY = auto()

    def __str__(self):
        return self.name


class TurnStep(Enum):
    UNKNOWN = 0
    CHECK_VICTORY = auto()
    TURN_NIGHT = auto()
    TURN_DAY = auto()
    ELECT = auto()
    VOTE_FOR_CAPTAIN = auto()
    VOTE = auto()

    def __str__(self):
        return self.name
