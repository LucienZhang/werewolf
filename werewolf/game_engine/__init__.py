from werewolf.utils.game_exceptions import GameFinished
from werewolf.utils.enums import GameEnum
from .game_api import join_game, setup_game, quit_game, deal, get_game_info, sit, next_step, vote, elect, wolf_kill, discover, witch, elixir, toxic, guard, shoot, suicide, handover


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
        'handover': handover,
    }

    @staticmethod
    def perform(cmd):
        try:
            return GameEngine.router[cmd]()
        except GameFinished:
            return GameEnum.OK.digest()
