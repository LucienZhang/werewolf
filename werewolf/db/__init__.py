from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)


class User(db.Model):
    __tablename__ = 'users'
    # name 'id' is preserved!
    uid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(length=255),
                         nullable=False, unique=True, index=True)
    password = db.Column(db.String(length=255), nullable=False)
    login_token = db.Column(db.String(length=255), nullable=False, index=True)
    nickname = db.Column(db.String(length=255), nullable=False)
    avatar = db.Column(db.Integer, nullable=False)
    gid = db.Column(db.Integer, nullable=False)  # gid=-1 means not in game

    @staticmethod
    def create_new_user(username, password, nickname, avatar):
        if User.query.filter_by(username=username).first() is not None:
            return None
        else:
            new_user = User(username=username, password=password, login_token='', nickname=nickname, avatar=avatar, gid=-1)
            db.session.add(new_user)
            db.session.commit()
        return new_user


class Game(db.Model):
    __tablename__ = 'games'
    gid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    host_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    victory_mode = db.Column(db.Integer, nullable=False)
    captain_mode = db.Column(db.Integer, nullable=False)
    witch_mode = db.Column(db.Integer, nullable=False)
    wolf_mode = db.Column(db.Integer, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    cards = db.Column(db.String(length=1023), nullable=False)
    days = db.Column(db.Integer, nullable=False)
    now_index = db.Column(db.Integer, nullable=False)
    step_cnt = db.Column(db.Integer, nullable=False)
    steps = db.Column(db.String(length=1023), nullable=False)
    history = db.Column(db.String(length=1023), nullable=False)
    captain_uid = db.Column(db.Integer, nullable=False)


class Role(db.Model):
    __tablename__ = 'roles'
    uid = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(length=255), nullable=False)
    role_type = db.Column(db.Integer, nullable=False)
    group_type = db.Column(db.Integer, nullable=False)
    alive = db.Column(db.Boolean, nullable=False)
    iscaptain = db.Column(db.Boolean, nullable=False)
    voteable = db.Column(db.Boolean, nullable=False)
    speakable = db.Column(db.Boolean, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    skills = db.Column(db.String(length=255), nullable=False)
    tags = db.Column(db.String(length=255), nullable=False)
    args = db.Column(db.String(length=255), nullable=False)

    @staticmethod
    def create_new_role(uid, nickname):
        existing_role = Role.query.get(uid)
        if existing_role is not None:
            existing_role.nickname = nickname
            existing_role.reset()
            db.session.add(existing_role)
            db.session.commit()
            return existing_role
        else:
            new_role = Role(uid=uid, nickname=nickname)
            new_role.reset()
            db.session.add(new_role)
            db.session.commit()
            return new_role

    # def reset(self):
    #     self.role_type = GameEnum.ROLE_TYPE_UNKNOWN.value
    #     self.group_type = GameEnum.GROUP_TYPE_UNKNOWN.value
    #     self.alive = True
    #     self.iscaptain = False
    #     self.voteable = True
    #     self.speakable = True
    #     self.position = -1
    #     self.skills = '[]'
    #     self.tags = '[]'
    #     self.args = '{}'
