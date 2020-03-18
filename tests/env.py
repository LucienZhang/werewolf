
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from werewolf import create_app
from werewolf.db import db


@pytest.fixture(scope='session')
def app():
    app = create_app('test')
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.drop_all()
