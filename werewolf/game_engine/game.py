# from __future__ import annotations

# from datetime import datetime, timedelta
# from werewolf.utils.enums import GameEnum, EnumMember
# import json
# from werewolf.utils.json_utils import json_hook, ExtendedJSONEncoder
# from werewolf.db import db
# from werewolf.game_module.role import Role
# from sqlalchemy.dialects.mysql import DATETIME
# import typing
# from typing import List
# from werewolf.utils.publisher import publish_music, publish_history, publish_info
# from werewolf.utils.scheduler import scheduler
# import collections
# from copy import deepcopy

# if typing.TYPE_CHECKING:
#     from werewolf.game_module.user import User





# class Game(object):
#     def __init__(self, table: GameTable = None, roles: List[Role] = None, steps: dict = None, cards: list = None,
#                  last_modified: datetime = None, history: dict = None, roles_loaded=False):
#         self.table = table
#         if roles is None:
#             self._roles = []
#         else:
#             self._roles = roles
#         if steps is None:
#             self._steps = {}
#         else:
#             self._steps = steps
#         self._cards = cards
#         if history is None:
#             self._history = {}
#         else:
#             self._history = history
#         self._last_modified = last_modified

#         self.roles_loaded = roles_loaded

#     def __enter__(self):
#         return self

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.commit()
#         return True if exc_type is None else False

#     def to_json(self) -> dict:
#         return {'gid': self.gid,
#                 'host_uid': self.host_uid,
#                 'status': [self.status.name, self.status.message],
#                 'victory_mode': self.victory_mode.name,
#                 'captain_mode': self.captain_mode.name,
#                 'witch_mode': self.witch_mode.name,
#                 'wolf_mode': self.wolf_mode.name,
#                 'roles': [[role.uid, role.position, role.name] for role in self.roles],
#                 'end_time': str(self.table.end_time),
#                 'last_modified': str(self.table.last_modified),
#                 'cards': [card.name for card in self.cards],
#                 'days': self.days,
#                 'now_index': self.now_index,
#                 'repeat': self.repeat,
#                 'steps': {
#                     'global_steps': self.steps['global_steps'],
#                     'step_list': [step.name for step in self.steps['step_list']]
#                 },
#                 'history': self.history,
#                 'captain_uid': self.captain_uid}



#     @staticmethod
#     def get_game_by_gid(gid, lock=False, load_roles=False):
#         if gid is None or gid == -1:
#             return None
#         if not lock:
#             game_table = GameTable.query.get(gid)
#             if game_table and datetime.utcnow() < game_table.end_time:
#                 roles = []
#                 if load_roles:
#                     uid_list = json.loads(game_table.roles)
#                     for uid in uid_list:
#                         r = Role.get_role_by_uid(uid)
#                         roles.append(r)
#                 steps = json.loads(game_table.steps, object_hook=json_hook)
#                 cards = json.loads(game_table.cards, object_hook=json_hook)
#                 history = Game._parse_history(game_table.history)
#                 return Game(table=game_table, roles=roles, steps=steps, cards=cards,
#                             history=history,
#                             last_modified=game_table.last_modified, roles_loaded=load_roles)
#             else:
#                 return None
#         else:
#             game_table = GameTable.query.with_for_update().get(gid)
#             if game_table and datetime.utcnow() < game_table.end_time:
#                 roles = []
#                 if load_roles:
#                     uid_list = json.loads(game_table.roles)
#                     for uid in uid_list:
#                         r = Role.get_role_by_uid(uid)
#                         roles.append(r)
#                 steps = json.loads(game_table.steps, object_hook=json_hook)
#                 cards = json.loads(game_table.cards, object_hook=json_hook)
#                 history = Game._parse_history(game_table.history)
#                 return Game(table=game_table, roles=roles, steps=steps, cards=cards,
#                             history=history,
#                             last_modified=game_table.last_modified, roles_loaded=load_roles)
#             else:
#                 db.session.commit()
#                 return None

#     @staticmethod
#     def _parse_history(history_json):
#         """
#             pos: -1=no one, -2=not acted
#             {
#                 'wolf_kill':{wolf_pos:target_pos,...},
#                 'wolf_kill_decision':pos,
#                 'elixir':True / False,
#                 'guard':pos,
#                 'toxic':pos,
#                 'discover':pos,
#                 'voter_votee':[[voter_pos,...],[votee_pos,...]],
#                 'vote_result': {voter_pos:votee_pos,...},
#                 'dying':{pos:True},
#             }
#         """
#         def _parse(d):
#             new_d = {}
#             for key, value in d.items():
#                 new_d[int(key)] = value
#             return new_d

#         history = json.loads(history_json)
#         if 'wolf_kill' in history:
#             history['wolf_kill'] = _parse(history['wolf_kill'])
#         if 'vote_result' in history:
#             history['vote_result'] = _parse(history['vote_result'])
#         if 'dying' in history:
#             history['dying'] = _parse(history['dying'])
#         return history

#     def commit(self) -> (bool, GameEnum):
#         # assert self._last_modified == self.table.last_modified
#         if self.roles_loaded:
#             self.table.roles = json.dumps(
#                 [r.uid for r in self.roles], cls=ExtendedJSONEncoder)
#         self.table.steps = json.dumps(self.steps, cls=ExtendedJSONEncoder)
#         self.table.cards = json.dumps(self.cards, cls=ExtendedJSONEncoder)
#         self.table.history = json.dumps(self.history)
#         db.session.add(self.table)
#         db.session.commit()
#         return True, None

    

#     def get_role_by_pos(self, pos):
#         pos = int(pos)
#         if pos < 0:
#             return None
#         if not self.roles_loaded:
#             uid = json.loads(self.table.roles)[pos - 1]
#             return self.get_role_by_uid(uid)
#         else:
#             for r in self.roles:
#                 if r.position == pos:
#                     return r
#             else:
#                 None

#     def get_role_by_uid(self, uid, with_index=False):
#         uid = int(uid)
#         if uid < 0:
#             return None
#         if not self.roles_loaded:
#             r = Role.get_role_by_uid(uid)
#             return (None, r) if with_index else r
#         else:
#             for i, r in enumerate(self.roles):
#                 if r.uid == uid:
#                     return (i, r) if with_index else r
#             else:
#                 return (None, None) if with_index else None

    

    

    

#   

#     def kill(self, target_pos: int, how: GameEnum):
#         if target_pos < 1 or target_pos > self.get_seat_num():
#             return
#         target_role = self.get_role_by_pos(target_pos)

#         # todo 长老?

#         if target_role is GameEnum.ROLE_TYPE_IDIOT and how is GameEnum.SKILL_VOTE and not target_role.args['exposed']:
#             target_role.args['exposed'] = True
#             target_role.voteable = False
#             target_role.commit()
#             return

#         dying = self.history['dying']
#         dying[target_role.position] = True

#         if how is GameEnum.SKILL_TOXIC and target_role is GameEnum.ROLE_TYPE_HUNTER:
#             target_role.args['shootable'] = False
#             target_role.commit()

#         # todo: other link die

#         self.check_win()






#     def calculate_die_in_night(self):
#         wolf_kill_pos = self.history['wolf_kill_decision']
#         elixir = self.history['elixir']
#         guard = self.history['guard']

#         if wolf_kill_pos > 0:
#             killed = True
#             if elixir:
#                 killed = not killed
#             if guard == wolf_kill_pos:
#                 killed = not killed

#             if killed:
#                 self.kill(wolf_kill_pos, GameEnum.SKILL_WOLF_KILL)
#         if self.history['toxic'] > 0:
#             self.kill(self.history['toxic'], GameEnum.SKILL_TOXIC)
#         # todo: other death way in night?

#     def check_win(self):
#         gods = wolves = villagers = 0
#         # todo third party?

#         for r in self.roles:
#             if not r.alive:
#                 continue

#             if r.group_type is GameEnum.GROUP_TYPE_VILLAGERS:
#                 villagers += 1
#             elif r.group_type is GameEnum.GROUP_TYPE_WOLVES:
#                 wolves += 1
#             elif r.group_type is GameEnum.GROUP_TYPE_GODS:
#                 if r.role_type is GameEnum.ROLE_TYPE_IDIOT and r.args['exposed']:
#                     continue
#                 gods += 1
#             else:
#                 raise Exception('Unknown Group!')

#         ended = False
#         if wolves == 0:
#             ended = True
#             publish_history(self.gid, '游戏结束，好人阵营胜利')
#             # todo result analysis
#         if gods == 0 and villagers == 0:
#             ended = True
#             publish_history(self.gid, '游戏结束，狼人阵营胜利')
#         elif self.witch_mode is GameEnum.VICTORY_MODE_KILL_GROUP and (gods == 0 or villagers == 0):
#             ended = True
#             publish_history(self.gid, '游戏结束，狼人阵营胜利')

#         # prepare for next round
#         if ended:
#             pass  # todo

#     def get_attackable_wolf(self):
#         attackable = []
#         for r in self.roles:
#             if r.alive and GameEnum.ROLE_TYPE_ALL_WOLF in r.tags:
#                 attackable.append(r)
#         return attackable


# def action_timeout(gid, global_step_num):
#     game = Game.get_game_by_gid(gid)
#     if global_step_num != game.steps['global_steps']:
#         return
#     game.go_next_step()
#     game.commit()
#     return
