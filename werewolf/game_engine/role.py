# from werewolf.db import db
# from werewolf.utils.enums import GameEnum, EnumMember
# import json
# from werewolf.utils.json_utils import ExtendedJSONEncoder, json_hook
# from copy import deepcopy





# class Role(object):
#     """Base Class"""

#     def __init__(self, table: RoleTable, skills: list = None, tags: list = None, args: dict = None):
#         self.table = table
#         if skills is None:
#             self._skills = []
#         else:
#             self._skills = skills
#         if tags is None:
#             self._tags = []
#         else:
#             self._tags = tags
#         if args is None:
#             self._args = {}
#         else:
#             self._args = args

#     def to_json(self) -> dict:
#         return {'uid': self.uid,
#                 'name': self.name,
#                 'role_type': [self.role_type.name, self.role_type.message],
#                 'group_type': self.group_type.name,
#                 'alive': self.alive,
#                 'iscaptain': self.iscaptain,
#                 'voteable': self.voteable,
#                 'speakable': self.speakable,
#                 'position': self.position,
#                 'skills': [[skill.name, skill.message] for skill in self.skills],
#                 'tags': [tag.name for tag in self.tags],
#                 'args': self.args}

#   

#     @staticmethod
#     def get_role_by_uid(uid):
#         if uid < 0:
#             return None
#         role_table = RoleTable.query.get(uid)
#         if role_table is not None:
#             skills = json.loads(role_table.skills, object_hook=json_hook)
#             tags = json.loads(role_table.tags, object_hook=json_hook)
#             args = json.loads(role_table.args, object_hook=json_hook)
#             return Role(role_table, skills, tags, args)
#         else:
#             return None

#     def commit(self) -> (bool, GameEnum):
#         self.table.skills = json.dumps(self._skills, cls=ExtendedJSONEncoder)
#         self.table.tags = json.dumps(self._tags, cls=ExtendedJSONEncoder)
#         self.table.args = json.dumps(self._args, cls=ExtendedJSONEncoder)
#         db.session.add(self.table)
#         db.session.commit()
#         return True, None

