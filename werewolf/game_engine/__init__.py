from .game_api import join_game, setup_game, quit_game, deal, get_game_info, sit, next_step, vote, elect, wolf_kill, discover, witch, elixir, toxic, guard, shoot, suicide


class GameEngine(object):
    router = {
        'join': join_game,
        'setup': setup_game,
        'quit': quit_game,
        'deal': deal,
        'get_game_info': get_game_info,
        'sit': sit,
        'next_step': next_step,
        'vote': vote,
        'elect': elect,
        'wolf_kill': wolf_kill,
        'discover': discover,
        'witch': witch,
        'elixir': elixir,
        'toxic': toxic,
        'guard': guard,
        'shoot': shoot,
        'suicide': suicide,
    }

    @staticmethod
    def perform(cmd):
        return GameEngine.router[cmd]()
