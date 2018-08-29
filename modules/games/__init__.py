import pickle
import time

import telepot

from ..base import Module

from .klaverjas_game import Klaverjas, KlaverjasDispatcher, KlaverjasChallenge, KLAVERJASSEN

#game_identifier = {KLAVERJASSEN: "k"}


class Games(Module):
    def initialise(self, bot):
        bot.games = {}
        games = bot.dataManager.get_active_games()
        for g in games:
            game = pickle.loads(g['game_data'])
            game.setstate(bot)
            bot.games[g['game_id']] = game

    def register_commands(self, bot):
        bot.add_slash_command("klaverjassen", self.klaverjassen)
        bot.add_slash_command("klaverchallenge", self.klaverchallenge)
        bot.add_slash_command("klaverchallenge4", self.klaverchallenge4)
        #bot.add_callback_query("gamestart", self.callbackstart)
        bot.add_callback_query("games", self.callback)

    def klaverjassen(self, bot, msg):
        ident = bot.dataManager.get_unique_game_id()
        if msg.chat_type == "private":
            g = Klaverjas(bot, ident, [(msg.sender,msg.sendername)], msg.date, msg.command.strip())
        else:
            g = KlaverjasDispatcher(bot, ident, msg)
        bot.games[ident] = g

    def klaverchallenge(self, bot, msg):
        ident = bot.dataManager.get_unique_game_id()
        g = KlaverjasChallenge(bot, ident, msg)
        bot.games[ident] = g

    def klaverchallenge4(self, bot, msg):
        ident = bot.dataManager.get_unique_game_id()
        g = KlaverjasChallenge(bot, ident, msg, ngames=4)
        bot.games[ident] = g

    def callback(self, bot, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        game_id, callback_id, button_id = [int(s) for s in data[5:].split(":")]
        g = bot.games[game_id]
        if not g.loaded: g.load()
        ident, func = g.callbacks[callback_id]
        s = func(ident, button_id,(msg['from']['id'],msg['from']['first_name']))
        if s: bot.telebot.answerCallbackQuery(query_id, s)

games = Games()
