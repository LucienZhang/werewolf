# # -*- coding: utf-8 -*-
# # @Author: Lucien Zhang
# # @Date:   2019-10-01 13:13:52
# # @Last Modified by:   Lucien Zhang
# # @Last Modified time: 2019-10-09 12:12:46
#
# from werewolf.utils.enums import RoleType, TurnStep, CaptainMode
# from collections import Counter
#
#
# class Turn(object):
#     def __init__(self, days=0, now=0, steps=None, repeat=0, card_dict=None, captain_mode=CaptainMode.UNKNOWN):
#         self.days = days
#         self.now = now
#         if steps is None:
#             self.steps = []
#         else:
#             self.steps = steps
#         self.repeat = repeat
#         if card_dict is not None:
#             self._reset(card_dict, captain_mode)
#
#     def _reset(self, card_dict, captain_mode):
#         self.days += 1
#         self.now = 0
#         self.repeat = 0
#         roles = Counter(card_dict).elements()
#         # roles = [RoleType[role] for role in roles]
#         self.steps.clear()
#         if self.days == 1 and RoleType.THIEF in roles:
#             pass
#         if self.days == 1 and RoleType.CUPID in roles:
#             pass
#         # TODO: 恋人互相确认身份
#         self.steps.append(RoleType.ALL_WOLF)
#         self.steps.append(RoleType.SEER)
#         self.steps.append(RoleType.WITCH)
#         self.steps.append(RoleType.SAVIOR)
#         self.steps.append(TurnStep.CHECK_VICTORY)
#         self.steps.append(TurnStep.TURN_DAY)
#
#         if self.days == 1 and captain_mode == CaptainMode.WITH_CAPTAIN:
#             self.steps.append(TurnStep.ELECT)
#             self.steps.append(TurnStep.VOTE_FOR_CAPTAIN)
#         self.steps.append(TurnStep.VOTE)
#         self.steps.append(TurnStep.CHECK_VICTORY)
#
#     def current_step(self):
#         ans = self.steps[self.now]
#         return ans, ans not in [TurnStep.CHECK_VICTORY]
#
#     def go_next_step(self, card_dict, captain_mode,):  # return if need to return the answer to user
#         if self.now == len(self.steps) - 1:
#             self._reset(card_dict, captain_mode)
#         else:
#             self.now += 1
#         return self.current_step()
