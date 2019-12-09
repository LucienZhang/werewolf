# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-16 17:44:43
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 15:01:42

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_required
from flask_sse import sse
from werewolf.game_module.game import Game
import json
from werewolf.login import do_login, do_logout, do_register
from werewolf.utils.enums import GameEnum
from werewolf.game_module import game_engine
from collections import Counter
from werewolf.utils.scheduler import scheduler
import datetime

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
        victory_mode = GameEnum('VICTORY_MODE_{}'.format(request.form['victoryMode'].upper()))
        captain_mode = GameEnum('CAPTAIN_MODE_{}'.format(request.form['captainMode'].upper()))
        witch_mode = GameEnum('WITCH_MODE_{}'.format(request.form['witchMode'].upper()))
        villager_cnt = int(request.form['villager'])
        normal_wolf_cnt = int(request.form['normal_wolf'])
        cards = [GameEnum.ROLE_TYPE_VILLAGER] * villager_cnt + [GameEnum.ROLE_TYPE_NORMAL_WOLF] * normal_wolf_cnt

        single_roles = request.form.getlist('single_roles')
        for r in single_roles:
            cards.append(GameEnum(f'ROLE_TYPE_{r.upper()}'))

        new_game = Game.create_new_game(host=current_user, victory_mode=victory_mode, cards=cards,
                                        captain_mode=captain_mode, witch_mode=witch_mode)

        current_user.game = new_game
        current_user.commit()

        return redirect(url_for('werewolf_api.join', gid=new_game.gid))


@werewolf_api.route('/game', methods=['GET'])
@login_required
def game():
    current_setting = []
    current_game = current_user.game
    current_setting.append('游戏模式为：' + current_game.victory_mode.message)
    current_setting.append('警长模式为：' + current_game.captain_mode.message)
    current_setting.append('女巫模式为：' + current_game.witch_mode.message)
    current_setting.append('游戏总人数为：' + str(current_game.get_seat_num()) + '人')
    for role, cnt in Counter(current_game.cards).items():
        current_setting.append(role.message + ' = ' + str(cnt))

    return render_template("werewolf_game.html", ishost=current_user.ishost, name=current_user.name,
                           gid=current_game.gid,
                           current_setting=current_setting,
                           role_name=current_user.role.role_type.message,
                           role_type=current_user.role.role_type.name.lower(),
                           seat_cnt=current_game.get_seat_num(),
                           dbtxt=(str(current_user.game.roles) + str(
                               type(current_user.game.roles)) + '\n<br />\n' + str(
                               current_user.game.days) + str(type(current_user.game.steps))))


@werewolf_api.route('/action')
@login_required
def action():
    return game_engine.take_action()


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
    success, e = current_user.join_game(gid)
    if success:
        return redirect(url_for('werewolf_api.game'))
    else:
        if e is GameEnum.GAME_MESSAGE_ALREADY_IN:
            return redirect(url_for('werewolf_api.game'))
        else:
            return e.message


@werewolf_api.route('/quit')
@login_required
def quit_game():
    success, e = current_user.quit_game()
    if success:
        return redirect(url_for('werewolf_api.home'))
    else:
        if e is GameEnum.GAME_MESSAGE_NOT_IN_GAME:
            return redirect(url_for('werewolf_api.home'))
        else:
            return e.message


@werewolf_api.route('/test')
def test():
    return render_template('test.html')


@werewolf_api.route('/send')
def send():
    # gid = request.args.get('gid')
    # sse.publish_music(json.dumps([url_for('werewolf_api.static', filename='audio/seer_start_voice.mp3'),
    #                         url_for('werewolf_api.static', filename='audio/night_bgm.mp3'), ]),
    #             type='music',
    #             channel=gid)
    seconds = request.args.get('s')
    msg = request.args.get('msg')
    scheduler.add_job(id='test_job', func=test_func, args=(msg,),
                      next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=int(seconds)))
    test_func('ping')
    return "Message sent!"


def test_func(msg='default message'):
    with scheduler.app.app_context():
        sse.publish({"message": msg}, type='greeting')
    return "Message sent!"
