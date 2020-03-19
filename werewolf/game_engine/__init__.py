from .game_api import join_game, setup_game, quit_game, deal, get_game_info


class GameEngine(object):
    router = {
        'join': join_game,
        'setup': setup_game,
        'quit': quit_game,
        'deal': deal,
        'get_game_info': get_game_info,
    }

    @staticmethod
    def perform(cmd):
        return GameEngine.router[cmd]()
