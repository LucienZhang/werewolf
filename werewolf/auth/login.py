from flask import render_template, request, redirect, url_for, flash, Response
from flask_login import LoginManager, current_user, login_user, logout_user
from werewolf.game_module.user import User, UserTable
from werewolf.game_module.game import Game
from flask import current_app
from werewolf.game_module.game import GameTable
from datetime import datetime
from hashlib import sha1
from werewolf.db import db
from werewolf.utils.enums import GameEnum


def generate_login_token(username):
    return sha1((current_app.config["LOGIN_SECRET_KEY"] + username + str(datetime.utcnow().timestamp())).encode(
        'utf-8')).hexdigest()


def init_login(app):
    login_manager = LoginManager(app)
    login_manager.login_view = 'werewolf_api.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(login_token):
        return User.get_user_by_token(login_token)


def user_login() -> dict:
    username = request.form.get('username')
    user = User.get_user_by_username(username)
    if user and request.form['password'] == user.table.password:
        user.id = user.table.login_token = generate_login_token(username)
        user.commit()
        login_user(user, remember=True)
        current_app.logger.info(f'User uid={user.uid} successfully logged in')
        return GameEnum.OK.digest()
    else:
        current_app.logger.info(f'User uid={user.uid} login failed')
        return GameEnum.GAME_MESSAGE_WRONG_PASSWORD.digest()


def user_logout() -> dict:
    uid = current_user.uid
    current_user.table.login_token = ""
    db.session.add(current_user.table)
    db.session.commit()
    logout_user()
    current_app.logger.info(f'User uid={uid} successfully logged out')
    return GameEnum.OK.digest()


def user_register() -> dict:
    existing_user = UserTable.query.filter_by(username=request.form['username']).first()
    if existing_user:
        return GameEnum.GAME_MESSAGE_USER_EXISTS.digest()
    else:
        user = User.create_new_user(username=request.form['username'], password=request.form['password'],
                                    nickname=request.form['nickname'], avatar=1)  # request.form['avatar'])
        return GameEnum.OK.digest()
