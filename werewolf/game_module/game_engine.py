# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-10-16 14:41:14
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-16 17:30:29

from flask import request, current_app
from flask_login import current_user
import json
from werewolf.utils.json_utils import JsonHook, ExtendJSONEncoder


def get_history():
    toget = int(request.args.get('toget'))
    return json.dumps(current_user.role.history[toget:], cls=ExtendJSONEncoder)


def get_audio():
    toget = int(request.args.get('toget'))
    return json.dumps(current_user.game.audio[toget:], cls=ExtendJSONEncoder)
