from urllib.parse import quote
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    pass


class DevelopmentConfig(Config):
    DEBUG = True
    PORT = 1000
    SECRET_KEY = '123456'
    # SQLALCHEMY_DATABASE_URI = "mysql://username:%s@127.0.0.1:3306/database?charset=utf8" % quote('password')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGIN_SECRET_KEY = '123456'
    REDIS_URL = "redis://localhost"
    SCHEDULER_API_ENABLED = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
