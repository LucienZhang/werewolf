from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf import create_app
from werewolf.database import db
from werewolf.database import User, Game, Role


app = create_app('db')
with app.app_context():
    # print(User.query.get(1))
    db.drop_all()
    db.create_all()
# db.drop_all(app=app)
# db.create_all(app=app)
