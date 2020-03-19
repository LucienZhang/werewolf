from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf import create_app
from werewolf.database import db


app = create_app('db')
with app.app_context():
    db.drop_all()
    db.create_all()
