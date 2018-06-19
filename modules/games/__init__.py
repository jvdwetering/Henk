import pickle

import telepot

from ..base import Module

from .klaverjas_game import Klaverjas, KLAVERJASSEN

game_identifier = {KLAVERJASSEN: "k"}


class Games(Module):
    def initialise(self, bot):
        self.games = {}
        games = bot.dataManager.get_active_games()
        for g in games:
            game = pickle.loads(g['game_data'])
            game.bot = bot #This info is not loaded by pickle
            self.games[g['game_id']] = game

    def register_commands(self, bot):
        '''
        should call 
        bot.add_slash_command("slashcommand", self.callback)
        bot.add_command_category("commandtype", self.callback)
        bot.add_callback_query("ident", self.callback)
        '''
        bot.add_slash_command("klaverjassen", self.klaverjassen)
        bot.add_callback_query("games", self.callback)

    def klaverjassen(self,bot,msg):
        # if msg.sender in self.active_users:
        #     if self.games[self.active_users[msg.sender]].is_active:
        #         return "Je bent al bezig met een potje"
        ident = len(bot.dataManager.games)
        g = Klaverjas(bot, ident, [(msg.sender,msg.sendername)], msg.date)
        self.games[ident] = g
        #self.active_users[msg.sender] = ident

    def callback(self, bot, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        game_id, callback_id, button_id = [int(s) for s in data[5:].split(":")]
        ident, func = self.games[game_id].callbacks[callback_id]
        func(ident, button_id)


    # def is_games_message(self, msg):
    #     if not msg.sender in self.active_users: return False
    #     game_id = self.active_users[msg.sender]
    #     g = self.games[game_id]
    #     ident = game_identifier[g.game_type]
    #     if msg.raw.startswith(ident) and len(msg.raw)==2:
    #         if msg.sender in g.current_users: return True
    #     return False

    # def parse_message(self, bot, msg):
    #     game_id = self.active_users[msg.sender]
    #     g = self.games[game_id]
    #     msg.command = msg.raw[1:]
    #     g.parse_message(msg)

games = Games()
