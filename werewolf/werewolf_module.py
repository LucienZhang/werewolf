from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import current_user, login_required
import functools
from flask_sse import sse
from werewolf.auth.login import user_login, user_logout, user_register
from werewolf.game_engine import GameEngine
from werewolf.database import Game, User, Role
from collections import Counter
from werewolf.game_engine.step_processor import StepProcessor
# from werewolf.utils.scheduler import scheduler
# import datetime

werewolf_api = Blueprint('werewolf_api', __name__)


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
        res = GameEngine.perform('setup')
        if res['msg'] != 'OK':
            flash(res['msg'], 'error')
            return render_template("werewolf_setup.html")
        else:
            return redirect(url_for('werewolf_api.join', gid=res['gid']))


@werewolf_api.route('/game', methods=['GET'])
@login_required
def game():
    current_setting = []
    current_game = Game.query.get(current_user.gid)
    current_setting.append('游戏模式为：' + current_game.victory_mode.label)
    current_setting.append('警长模式为：' + current_game.captain_mode.label)
    current_setting.append('女巫模式为：' + current_game.witch_mode.label)
    current_setting.append('游戏总人数为：' + str(current_game.get_seats_cnt()) + '人')
    for role, cnt in Counter(current_game.cards).items():
        current_setting.append(role.label + ' = ' + str(cnt))

    current_role = Role.query.get(current_user.uid)
    return render_template("werewolf_game.html",
                           ishost=current_user.uid == current_game.host_uid,
                           nickname=current_user.nickname,
                           gid=current_game.gid,
                           uid=current_user.uid,
                           current_setting=current_setting,
                           role_name=current_role.role_type.label,
                           role_type=current_role.role_type.name.lower().replace('role_type_', '', 1),
                           seat_cnt=current_game.get_seats_cnt(),
                           days=current_game.days,
                           game_status=current_game.status,
                           skills=current_role.skills,
                           next_step=StepProcessor.get_instruction_string(current_game) or '等待中',
                           dbtxt=(str(current_game.players) + str(
                               type(current_game.players)) + '\n<br />\n' + str(type(current_game.steps))))


@werewolf_api.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        res = user_login()
        if res['msg'] != 'OK':
            flash(res['msg'], 'error')
            return render_template('login.html')
        else:
            return redirect(request.args.get('next') or url_for('werewolf_api.home'))


@werewolf_api.route('/logout')
@login_required
def logout():
    return jsonify(user_logout())


@werewolf_api.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        res = user_register()
        if res['msg'] != 'OK':
            flash(res['msg'], 'error')
            return render_template('register.html')
        else:
            return render_template('register_success.html')


@werewolf_api.route('/api/<string:cmd>', methods=['GET'])
@login_required
def api(cmd):
    return jsonify(GameEngine.perform(cmd))


@werewolf_api.route('/join')
@login_required
def join():
    res = GameEngine.perform('join')
    if res['msg'] != 'OK':
        if res['msg'] == GameEngine.GAME_MESSAGE_ALREADY_IN.label:
            return redirect(url_for('werewolf_api.game'))
        else:
            flash(res['msg'], 'error')
            return redirect(url_for('werewolf_api.home'))
    else:
        return redirect(url_for('werewolf_api.game'))


@werewolf_api.route('/quit')
@login_required
def quit_game():
    res = GameEngine.perform('quit')
    if res['msg'] != 'OK':
        flash(res['msg'], 'error')
        return redirect(url_for('werewolf_api.home'))
    else:
        return redirect(url_for('werewolf_api.home'))


def test_api(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not current_app.config["DEBUG"]:
            abort(403)
        else:
            return func(*args, **kwargs)
    return wrapper

#######################################
# Test API
#######################################


@test_api
@werewolf_api.route('/test/<string:cmd>', methods=['GET'])
def test(cmd):
    if cmd == 'home':
        return render_template('test.html', uid=1)
    else:
        sse.publish({"message": cmd}, type='greeting', channel='u1')


# #######################################
# # Test API
# #######################################
# @werewolf_api.route('/test')
# def test():
#     cmd = request.args.get('cmd')
#     if cmd == 'get_info':
#         game = Game.get_game_by_gid(current_user.gid, load_roles=True)
#         role = Role.get_role_by_uid(current_user.uid)
#         ret = {'user': current_user.to_json()}
#         if game:
#             ret['game'] = game.to_json()
#         if role:
#             ret['role'] = role.to_json()
#         return json.dumps(ret)


# @werewolf_api.route('/test_page')
# def test_page():
#     return render_template('test.html', uid=1)


# @werewolf_api.route('/send')
# def send():
#     # gid = request.args.get('gid')
#     # sse.publish_music(json.dumps([url_for('werewolf_api.static', filename='audio/seer_start_voice.mp3'),
#     #                         url_for('werewolf_api.static', filename='audio/night_bgm.mp3'), ]),
#     #             type='music',
#     #             channel=gid)
#     seconds = request.args.get('s')
#     msg = request.args.get('msg')
#     scheduler.add_job(id='test_job', func=test_func, args=(msg,),
#                       next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=int(seconds)))
#     test_func('ping')
#     return "Message sent!"


# def test_func(msg='default message'):
#     with scheduler.app.app_context():
#         sse.publish({"message": msg}, type='greeting', channel='u1')
#     return "Message sent!"
