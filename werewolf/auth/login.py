from flask import render_template, request, redirect, url_for, flash, Response
from flask_login import LoginManager, current_user, login_user, logout_user
from flask import current_app
from datetime import datetime
from hashlib import sha1
from werewolf.database import db
from werewolf.utils.enums import GameEnum
from werewolf.database import User, Role
from sqlalchemy.exc import IntegrityError


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
        if not login_token:
            return None
        return User.query.filter_by(login_token=login_token).first()


def user_login() -> dict:
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    if user and request.form['password'] == user.password:
        user.id = user.login_token = generate_login_token(username)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        current_app.logger.info(f'User uid={user.uid} successfully logged in')
        return GameEnum.OK.digest()
    else:
        current_app.logger.info(f'User username={username} login failed')
        return GameEnum.GAME_MESSAGE_WRONG_PASSWORD.digest()


def user_logout() -> dict:
    uid = current_user.uid
    current_user.login_token = ""
    db.session.add(current_user)
    db.session.commit()
    logout_user()
    current_app.logger.info(f'User uid={uid} successfully logged out')
    return GameEnum.OK.digest()


def user_register() -> dict:
    avatar = 1
    new_user = User(username=request.form['username'], password=request.form['password'], login_token='', nickname=request.form['nickname'], avatar=avatar, gid=-1)
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return GameEnum.GAME_MESSAGE_USER_EXISTS.digest()

    new_role = Role(uid=new_user.uid, nickname=new_user.nickname, avatar=avatar, gid=-1)
    new_role.reset()
    db.session.add(new_role)
    db.session.commit()
    return GameEnum.OK.digest()
