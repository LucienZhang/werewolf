from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf import create_app
from werewolf.db import db

from werewolf.game_module.game import GameTable
from werewolf.game_module.user import UserTable
from werewolf.game_module.role import RoleTable


app = create_app('db')
db.drop_all(app=app)
db.create_all(app=app)
