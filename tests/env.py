
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf import create_app
from werewolf.db import db

app = create_app('test')
app.testing = True
app.app_context().push()


@pytest.fixture(scope='session')
def init_table():
    db.drop_all()
    db.create_all()
