# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-16 17:44:43
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 15:01:42

from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for
from flask_login import current_user, login_required
from flask_sse import sse
from werewolf.game_module.user import User, UserTable
from werewolf.game_module.game import Game, GameTable
from werewolf.game_module.role import Role
import time
import json
from werewolf.login import do_login, do_logout, do_register
from werewolf.utils.enums import VictoryMode, RoleType, CaptainMode, WitchMode
from werewolf.db import db
from werewolf.game_module.game_message import GameMessage
from werewolf.game_module import game_engine

werewolf_api = Blueprint('werewolf_api', __name__, template_folder='templates', static_folder='static')


@werewolf_api.route('/')
def home():
    return render_template("werewolf_home.html")


@werewolf_api.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if request.method == 'GET':
        # TODO: ask to quick existing game if user is in a game!
        return render_template("werewolf_setup.html")
    else:
        victory_mode = VictoryMode[request.form['victoryMode'].upper()]
        captain_mode = CaptainMode[request.form['captainMode'].upper()]
        witch_mode = WitchMode[request.form['witchMode'].upper()]
        villager_cnt = int(request.form['villager'])
        normal_wolf_cnt = int(request.form['normal_wolf'])
        card_dict = {}
        card_dict[RoleType.VILLAGER] = villager_cnt
        card_dict[RoleType.NORMAL_WOLF] = normal_wolf_cnt

        single_roles = request.form.getlist('single_roles')
        for r in single_roles:
            card_dict[RoleType[r.upper()]] = 1

        new_game = Game.create_new_game(host=current_user, victory_mode=victory_mode, card_dict=card_dict,
                                        captain_mode=captain_mode, witch_mode=witch_mode)

        current_user.game = new_game
        current_user.commit()

        return redirect(url_for('werewolf_api.join', gid=new_game.gid))


@werewolf_api.route('/game', methods=['GET'])
@login_required
def game():
    current_setting = []
    current_game = current_user.game
    current_setting.append('游戏模式为：' + GameMessage(current_game.victory_mode).parse())
    current_setting.append('警长模式为：' + GameMessage(current_game.captain_mode).parse())
    current_setting.append('女巫模式为：' + GameMessage(current_game.witch_mode).parse())
    current_setting.append('游戏总人数为：' + str(current_game.get_seat_num()) + '人')
    for role, cnt in current_game.card_dict.items():
        current_setting.append(GameMessage(role).parse() + ' = ' + str(cnt))

    return render_template("werewolf_game.html", ishost=current_user.ishost, name=current_user.name,
                           gid=current_game.gid,
                           current_setting=current_setting,
                           role_name=GameMessage(current_user.role.role_type).parse(),
                           role_type=current_user.role.role_type.name.lower(),
                           seat_cnt=current_game.get_seat_num(),
                           dbtxt=(str(current_user.game.roles) + str(
                               type(current_user.game.roles)) + '\n<br />\n' + str(
                               current_user.game.days) + str(type(current_user.game.steps))))


@werewolf_api.route('/action')
@login_required
def action():
    ret_message = game_engine.take_action()
    return ret_message.parse()


@werewolf_api.route('/login', methods=['GET', 'POST'])
def login():
    return do_login()


@werewolf_api.route('/logout')
@login_required
def logout():
    return do_logout()


@werewolf_api.route('/register', methods=['GET', 'POST'])
def register():
    return do_register()


@werewolf_api.route('/join')
@login_required
def join():
    gid = int(request.args.get('gid'))
    success, message = current_user.join_game(gid)
    if success:
        return redirect(url_for('werewolf_api.game'))
    else:
        if message.key == 'ALREADY_IN':
            return redirect(url_for('werewolf_api.game'))
        else:
            return message.parse()


@werewolf_api.route('/quit')
@login_required
def quit_game():
    success, message = current_user.quit_game()
    if success:
        return redirect(url_for('werewolf_api.home'))
    else:
        if message.key == 'NOT_IN_GAME':
            return redirect(url_for('werewolf_api.home'))
        else:
            return message.parse()


@werewolf_api.route('/test')
def test():
    return render_template('test.html')


@werewolf_api.route('/send')
def send():
    gid = request.args.get('gid')
    sse.publish(json.dumps([url_for('werewolf_api.static', filename='audio/seer_start_voice.mp3'),
                            url_for('werewolf_api.static', filename='audio/night_bgm.mp3'), ]),
                type='music',
                channel=gid)
    return "Message sent!"
