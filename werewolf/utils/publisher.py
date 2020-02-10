from flask import url_for
from flask_sse import sse
import json


def publish_music(instruction, bgm, channel, repeat=True):
    instruction = url_for('werewolf_api.static', filename=f'audio/{instruction}.mp3')
    if bgm not in ['same', 'stop']:
        bgm = url_for('werewolf_api.static', filename=f'audio/{bgm}.mp3')
    sse.publish(json.dumps([instruction, bgm, repeat]),
                type='music',
                channel=channel)


def publish_history(channel, message, show=True):
    publish_info(channel, json.dumps({'history': message, 'show': show}))


def publish_info(channel, message):
    # message has to be a JSON string
    sse.publish(message,
                type='game_info',
                channel=channel)
