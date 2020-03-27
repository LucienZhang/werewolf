from flask import url_for
from flask_sse import sse
import json


def publish_music(channel, instruction, bgm, bgm_loop):
    instruction = url_for('static', filename=f'audio/{instruction}.mp3')
    if bgm is not None:
        bgm = url_for('static', filename=f'audio/{bgm}.mp3')
    sse.publish(json.dumps([instruction, bgm, bgm_loop]),
                type='music',
                channel=channel)


def publish_history(game, message, show=True):
    publish_info(game.gid, json.dumps({'history': message, 'days': game.days, 'game_status': game.status, 'show': show}))


def publish_info(channel, message):
    # message has to be a JSON string
    sse.publish(message,
                type='game_info',
                channel=channel)
