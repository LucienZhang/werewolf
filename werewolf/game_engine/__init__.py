from .game_api import join_game, setup_game


class GameEngine(object):
    router = {
        'join': join_game,
        'setup': setup_game,
    }

    @staticmethod
    def perform(cmd):
        return GameEngine.router[cmd]()
