# -*- coding: utf-8 -*-
# @Author: Lucien Zhang
# @Date:   2019-09-30 16:11:15
# @Last Modified by:   Lucien Zhang
# @Last Modified time: 2019-10-02 15:48:01

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
