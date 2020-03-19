import os


class Config:
    pass


class TestConfig(Config):
    DEBUG = True
    SECRET_KEY = '123456'
    SQLALCHEMY_DATABASE_URI = r'sqlite:///:memory:'
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
    GUNICORN = False


config = {
    'test': TestConfig,
    'db': DBConfig
}
