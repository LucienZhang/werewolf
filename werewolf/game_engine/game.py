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

#     @property
#     def gid(self):
#         return self.table.gid

#     @property
#     def host_id(self):
#         return self.table.host_id

#     @property
#     def status(self):
#         return GameEnum(self.table.status)

#     @status.setter
#     def status(self, status: EnumMember):
#         self.table.status = status.value

#     @property
#     def victory_mode(self):
#         return GameEnum(self.table.victory_mode)

#     @property
#     def captain_mode(self):
#         return GameEnum(self.table.captain_mode)

#     @property
#     def witch_mode(self):
#         return GameEnum(self.table.witch_mode)

#     @property
#     def wolf_mode(self):
#         return GameEnum(self.table.wolf_mode)

#     @property
#     def roles(self):
#         return self._roles

#     @property
#     def days(self):
#         return self.table.days

#     @days.setter
#     def days(self, days: int):
#         self.table.days = days

#     @property
#     def now_index(self):
#         return self.table.now_index

#     @now_index.setter
#     def now_index(self, now_index: int):
#         self.table.now_index = now_index

#     @property
#     def repeat(self):
#         return self.table.repeat

#     @repeat.setter
#     def repeat(self, repeat: int):
#         self.table.repeat = repeat

#     @property
#     def steps(self):
#         return self._steps

#     @steps.setter
#     def steps(self, steps: dict):
#         """
#         {
#             'global_steps':0,
#             'step_list':[EnumMember,...]
#         }
#         """
#         self._steps = steps

#     @property
#     def cards(self):
#         return self._cards

#     @property
#     def history(self):
#         return self._history

#     @history.setter
#     def history(self, history: dict):
#         self._history = history

#     @property
#     def captain_uid(self):
#         return self.table.captain_uid

#     @captain_uid.setter
#     def captain_uid(self, captain_uid: int):
#         self.table.captain_uid = captain_uid

    
#     # @staticmethod
#     # def create_game_from_table(game_table):
#     #     if game_table and datetime.utcnow() < game_table.end_time:
#     #         uid_list = json.loads(game_table.roles)
#     #         roles = []
#     #         for uid in uid_list:
#     #             r = Role.get_role_by_uid(uid)
#     #             roles.append(r)
#     #         steps = json.loads(game_table.steps, object_hook=json_hook)
#     #         cards = json.loads(game_table.cards, object_hook=json_hook)
#     #         return Game(table=game_table, roles=roles, steps=steps, cards=cards,
#     #                     last_modified=game_table.last_modified)
#     #     else:
#     #         return None

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

    

    

    

#     def _process_vote(self, vote_type):
#         # pos: -1=no one, -2=not acted
#         # 'vote_result': {voter_pos:votee_pos,...},
#         assert vote_type in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_CAPTAIN_VOTE,
#                              GameEnum.TURN_STEP_PK_VOTE, GameEnum.TURN_STEP_CAPTAIN_PK_VOTE]
#         msg = ""
#         result = {}
#         history_result = self.history['vote_result']
#         captain = self.get_role_by_uid(self.captain_uid)

#         captain_pos = captain.position if captain else -1

#         no_one = []
#         all_voters = set(self.history['voter_votee'][0])

#         for voter, votee in history_result.items():
#             all_voters.remove(voter)
#             if votee in [-1, -2]:
#                 no_one.append(voter)
#                 continue
#             if votee in result:
#                 result[votee].append(voter)
#             else:
#                 result[votee] = [voter]

#         no_one.extend(list(all_voters))
#         no_one.sort()

#         for votee in sorted(result.keys()):
#             msg += f'{votee} <= {",".join(map(str,list(sorted(result[votee]))))}\n'

#         if no_one:
#             msg += f'弃票： {",".join(map(str,no_one))}\n'

#         most_voted = []
#         max_ticket = 0
#         for votee in result:
#             ticket = len(result[votee])
#             if captain_pos in result[votee]:
#                 ticket += 0.5
#             if ticket == max_ticket:
#                 most_voted.append(votee)
#             elif ticket > max_ticket:
#                 max_ticket = ticket
#                 most_voted = [votee]
#             else:
#                 continue
#         if len(most_voted) == 1:
#             if vote_type in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_PK_VOTE]:
#                 msg += f'{most_voted[0]}号玩家以{max_ticket}票被公投出局'
#                 self.kill(most_voted[0], GameEnum.SKILL_VOTE)
#             else:
#                 captain = self.get_role_by_pos(most_voted[0])
#                 captain.iscaptain = True
#                 captain.commit()
#                 self.captain_uid = captain.uid
#                 msg += f'{most_voted[0]}号玩家以{max_ticket}票当选警长'
#             publish_history(self.gid, msg)
#             return
#         elif len(most_voted) == 0:
#             # all abstention, PK
#             if vote_type in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_CAPTAIN_VOTE]:
#                 if vote_type is GameEnum.TURN_STEP_VOTE:
#                     self.insert_step(GameEnum.TURN_STEP_PK_VOTE)
#                     self.insert_step(GameEnum.TURN_STEP_PK_TALK)
#                     voters, votees = self._generate_voter_votee(GameEnum.TURN_STEP_PK_VOTE, self.history['voter_votee'][1])
#                 else:
#                     self.insert_step(GameEnum.TURN_STEP_CAPTAIN_PK_VOTE)
#                     self.insert_step(GameEnum.TURN_STEP_CAPTAIN_PK_TALK)
#                     voters, votees = self._generate_voter_votee(GameEnum.TURN_STEP_CAPTAIN_PK_VOTE, self.history['voter_votee'][1])
#                 # 'voter_votee':[[voter_pos,...],[votee_pos,...]],
#                 self.history['voter_votee'] = [voters, votees]
#                 msg += f'以下玩家以{max_ticket}票平票进入PK：{",".join(map(str,votees))}'
#                 publish_history(self.gid, msg)
#                 return
#             else:
#                 raise Exception('It is impossible to have on one voted in PK')
#         else:
#             # PK
#             if vote_type in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_CAPTAIN_VOTE]:
#                 if vote_type is GameEnum.TURN_STEP_VOTE:
#                     self.insert_step(GameEnum.TURN_STEP_PK_VOTE)
#                     self.insert_step(GameEnum.TURN_STEP_PK_TALK)
#                     voters, votees = self._generate_voter_votee(GameEnum.TURN_STEP_PK_VOTE, most_voted)
#                 else:
#                     self.insert_step(GameEnum.TURN_STEP_CAPTAIN_PK_VOTE)
#                     self.insert_step(GameEnum.TURN_STEP_CAPTAIN_PK_TALK)
#                     voters, votees = self._generate_voter_votee(GameEnum.TURN_STEP_CAPTAIN_PK_VOTE, most_voted)
#                 # 'voter_votee':[[voter_pos,...],[votee_pos,...]],
#                 self.history['voter_votee'] = [voters, votees]
#                 msg += f'以下玩家以{max_ticket}票平票进入PK：{",".join(map(str,votees))}'
#                 publish_history(self.gid, msg)
#                 return
#             else:
#                 most_voted.sort()
#                 msg += f'以下玩家以{max_ticket}票再次平票：{",".join(map(str,most_voted))}\n'
#                 if vote_type is GameEnum.TURN_STEP_PK_VOTE:
#                     msg += '今天是平安日，无人被公投出局'
#                 else:
#                     msg += '警徽流失，本局游戏无警长'
#                 publish_history(self.gid, msg)
#                 return

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

#     def _generate_voter_votee(self, purpose, even_votees: list = None):
#         # only used for normal vote, not for captain
#         assert self.roles_loaded
#         voters = []
#         votees = []
#         if purpose is GameEnum.TURN_STEP_VOTE:
#             for r in self.roles:
#                 if r.alive and r.voteable:
#                     voters.append(r.position)
#                 if r.alive:
#                     votees.append(r.position)
#         elif purpose is GameEnum.TURN_STEP_PK_VOTE:
#             assert even_votees
#             votees = even_votees.copy()
#             for r in self.roles:
#                 if r.alive and r.voteable and r.position not in votees:
#                     voters.append(r.position)
#         elif purpose is GameEnum.TURN_STEP_CAPTAIN_VOTE:
#             for r in self.roles:
#                 if r.alive and GameEnum.TAG_ELECT in r.tags:
#                     votees.append(r.position)
#                 elif r.alive and r.voteable and GameEnum.TAG_NOT_ELECT in r.tags:
#                     voters.append(r.position)
#         elif purpose is GameEnum.TURN_STEP_CAPTAIN_PK_VOTE:
#             assert even_votees
#             votees = even_votees.copy()
#             for r in self.roles:
#                 if r.alive and r.voteable and r.position not in votees:
#                     voters.append(r.position)
#         else:
#             raise TypeError(f'Unknown purpose for voting: {purpose.name}')

#         voters.sort()
#         votees.sort()
#         return voters, votees

#     def _leave_current_step(self):
#         now = self.current_step()
#         if not now:
#             return
#         if now is GameEnum.TURN_STEP_ELECT:
#             for r in self.roles:
#                 if GameEnum.TAG_ELECT not in r.tags and GameEnum.TAG_NOT_ELECT not in r.tags:
#                     r.tags.append(GameEnum.TAG_NOT_ELECT)
#             voters, votees = self._generate_voter_votee(GameEnum.TURN_STEP_CAPTAIN_VOTE)
#             if len(votees) == 0:
#                 # no captain
#                 self.omit_step(2)
#                 publish_history(self.gid, '没有人竞选警长，本局游戏无警长')
#                 return
#             elif len(voters) == 0:
#                 # no captain
#                 self.omit_step(2)
#                 publish_history(self.gid, '所有人都竞选警长，本局游戏无警长')
#                 return
#             elif len(votees) == 1:
#                 # auto win captain
#                 self.omit_step(2)
#                 captain = votees[0]
#                 captain.iscaptain = True
#                 captain.commit()
#                 self.captain_uid = captain.uid
#                 publish_history(self.gid, f'只有{captain.position}号玩家竞选警长，自动当选')
#             else:
#                 publish_history(self.gid, f"竞选警长的玩家为：{','.join(map(str,votees))}\n未竞选警长的玩家为：{','.join(map(str,voters))}")
#                 self.history['voter_votee'] = [voters, votees]
#         elif now in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_CAPTAIN_VOTE, GameEnum.TURN_STEP_PK_VOTE, GameEnum.TURN_STEP_CAPTAIN_PK_VOTE]:
#             self._process_vote(now)
#         elif now is GameEnum.ROLE_TYPE_ALL_WOLF:
#             publish_music('wolf_end_voice', 'stop', self.gid)
#         elif now is GameEnum.ROLE_TYPE_SEER:
#             publish_music('seer_end_voice', 'stop', self.gid)
#             return True, None
#         elif now is GameEnum.ROLE_TYPE_WITCH:
#             publish_music('witch_end_voice', 'stop', self.gid)
#             return True, None
#         elif now is GameEnum.ROLE_TYPE_SAVIOR:
#             publish_music('savior_end_voice', 'stop', self.gid)
#             return True, None

#     def _execute_next_step(self):
#         self.steps['global_steps'] += 1

#         self.now_index += 1
#         if self.now_index >= len(self.steps['step_list']):
#             self.now_index = 0
#             self.steps['step_list'] = Game._reset_step_list(
#                 self.days, self.cards, self.captain_mode)

#         # current step
#         now = self.current_step()
#         if now is GameEnum.TURN_STEP_TURN_NIGHT:
#             for d in self.history['dying']:
#                 r = self.get_role_by_pos(d)
#                 r.alive = False
#                 r.commit()
#             self.history['dying'].clear()

#             publish_music('night_start_voice', 'night_bgm', self.gid)
#             self.reset_history()
#             self.status = GameEnum.GAME_STATUS_NIGHT
#             self.days += 1
#             publish_info(self.gid, json.dumps({'days': self.days, 'game_status': self.status.message}))
#             return self.go_next_step()
#         elif now is GameEnum.ROLE_TYPE_ALL_WOLF:
#             publish_music('wolf_start_voice', 'wolf_bgm', self.gid)
#             # todo: add random job if there is not wolf (third party situation)
#             # scheduler.add_job(id=f'{self.gid}_WOLF_KILL', func=action_timeout,
#             #                   args=(self.gid, self.steps['global_steps']),
#             #                   next_run_time=datetime.now() + timedelta(seconds=30))

#             # two mode:
#             # 1. without third party: any wolf kill is fine
#             # 2. with thrid party: all wolf kill is needed
#             return True, None
#         elif now in [GameEnum.TURN_STEP_TALK, GameEnum.TURN_STEP_ELECT_TALK]:
#             self.repeat = 0
#         elif now in [GameEnum.TURN_STEP_TALK, GameEnum.TURN_STEP_ELECT]:
#             publish_music('elect', 'stop', self.gid, repeat=False)
#         elif now in [GameEnum.TURN_STEP_VOTE, GameEnum.TURN_STEP_CAPTAIN_VOTE, GameEnum.TURN_STEP_PK_VOTE, GameEnum.TURN_STEP_CAPTAIN_PK_VOTE]:
#             self.history['vote_result'].clear()
#         elif now is GameEnum.TURN_STEP_ANNOUNCE:
#             if self.history['dying']:
#                 publish_history(self.gid, GameEnum.GAME_MESSAGE_DIE_IN_NIGHT.message.format(
#                     '，'.join(map(str, list(sorted(self.history['dying']))))))
#             else:
#                 publish_history(self.gid, "昨晚是平安夜")
#             self.history['voter_votee'] = self._generate_voter_votee(GameEnum.TURN_STEP_VOTE)
#             return self.go_next_step()
#         elif now is GameEnum.TURN_STEP_TURN_DAY:
#             publish_music('day_start_voice', 'day_bgm', self.gid, repeat=False)
#             self.status = GameEnum.GAME_STATUS_DAY
#             publish_info(self.gid, json.dumps({'game_status': self.status.message}))
#             self.calculate_die_in_night()
#             return self.go_next_step()
#         elif now is GameEnum.ROLE_TYPE_SEER:
#             publish_music('seer_start_voice', 'seer_bgm', self.gid)
#             return True, None
#         elif now is GameEnum.ROLE_TYPE_WITCH:
#             publish_music('witch_start_voice', 'witch_bgm', self.gid)
#             return True, None
#         elif now is GameEnum.ROLE_TYPE_SAVIOR:
#             publish_music('savior_start_voice', 'savior_bgm', self.gid)
#             return True, None

#     def go_next_step(self) -> (bool, GameEnum):
#         self._leave_current_step()
#         self._execute_next_step()

#     def current_step(self):
#         if self.now_index < 0:
#             return None
#         return self.steps['step_list'][self.now_index]

#     def insert_step(self, step):
#         self.steps['step_list'].insert(self.now_index + 1, step)
#         return

#     def omit_step(self, num):
#         for _ in range(num):
#             self.steps['step_list'].pop(self.now_index + 1)

#     def reset_history(self):
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
#         self.history = {
#             'wolf_kill': {},
#             'wolf_kill_decision': -2,
#             'elixir': False,
#             'guard': -2,
#             'toxic': -2,
#             'discover': -2,
#             'voter_votee': [[], []],
#             'vote_result': {},
#             'dying': {},
#         }

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
