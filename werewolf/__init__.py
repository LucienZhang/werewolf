import os
import logging
from flask import Flask, redirect, url_for
from flask_sse import sse
from werewolf.werewolf_module import werewolf_api
from werewolf.login import init_login
from werewolf.db import init_db
from werewolf.config import config
from werewolf.utils.scheduler import init_scheduler


def init_app(app):
    init_login(app)
    init_db(app)
    init_scheduler(app)
    app.register_blueprint(sse, url_prefix='/stream')
    # todo: access control
    # def check_access():
    # if request.args.get("channel") == "analytics" and not g.user.is_admin():
    #     abort(403)


def create_app(config_name=None):
    # create and configure the app
    root_path = os.path.abspath(os.path.dirname(__file__))
    app = Flask(__name__, instance_relative_config=True, root_path=root_path,
                instance_path=os.path.join(root_path, 'instance'))
    if config_name:
        app.config.from_object(config[config_name])
    else:
        app.config.from_pyfile('config.py', silent=True)

    if app.config["DEBUG"]:
        @app.after_request
        def after_request(response):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
            response.headers["Expires"] = 0
            response.headers["Pragma"] = "no-cache"
            return response

    if app.config["GUNICORN"]:
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    app.register_blueprint(werewolf_api, url_prefix='/werewolf')
    init_app(app)

    @app.route('/')
    def homepage():
        return redirect(url_for('werewolf_api.home'))

    return app
