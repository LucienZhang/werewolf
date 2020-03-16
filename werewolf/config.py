import os
from pathlib import Path
test_dir = Path(__file__).resolve().parent


class Config:
    pass


class TestConfig(Config):
    DEBUG = True
    SECRET_KEY = '123456'
    SQLALCHEMY_DATABASE_URI = r'sqlite:///' + str(test_dir / 'test_sqlite.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    LOGIN_SECRET_KEY = '123456'
    TESTING = True
    GUNICORN = False


class DBConfig(Config):
    DEBUG = False
    PORT = 1000
    SECRET_KEY = '123456'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    LOGIN_SECRET_KEY = '123456'
    REDIS_URL = "redis://localhost"
    SCHEDULER_API_ENABLED = True


config = {
    'test': TestConfig,
    'db': DBConfig
}
