# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-30 14:38:30
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-06 20:40:04

from flask import render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_user, logout_user
from werewolf.game_module.user import User, UserTable
from werewolf.game_module.game import Game
from flask import current_app
from werewolf.game_module.game import GameTable
from datetime import datetime
from hashlib import sha1
from werewolf.db import db


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

    @login_manager.request_loader
    def load_user_from_request(current_request):
        login_token = current_request.args.get('token')
        return User.get_user_by_token(login_token)


def do_login():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.get_user_by_username(username)
        if user and request.form['password'] == user.table.password:
            user.id = user.table.login_token = generate_login_token(username)
            user.commit()
            # 通过Flask-Login的login_user方法登录用户
            login_user(user, remember=True)
            # 如果请求中有next参数，则重定向到其指定的地址，
            # 没有next参数，则重定向到"home"视图
            current_app.logger.info(f'{username} login successfully!')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('werewolf_api.home'))
        else:
            current_app.logger.info(f'{username} login failed!')
            flash('用户名或密码错误', 'error')
            return render_template('login.html')
    else:
        # GET 请求
        return render_template('login.html')


def do_logout():
    username = current_user.name
    current_user.table.login_token = ""
    db.session.add(current_user.table)
    db.session.commit()
    logout_user()
    current_app.logger.info(f'{username} logout successfully!')

    return 'Logged out successfully!'


def do_register():
    if request.method == 'POST':
        existing_user = UserTable.query.filter_by(username=request.form['username']).first()
        if existing_user:
            flash('用户名已存在', 'error')
            return render_template('register.html')
        else:
            user = User.create_new_user(username=request.form['username'], password=request.form['password'],
                                        name=request.form['name'], avatar=1)  # request.form['avatar'])
            if not user:
                flash('未知错误，无法注册', 'error')
                return render_template('register.html')
            else:
                return render_template('register_success.html')
    else:
        return render_template('register.html')
