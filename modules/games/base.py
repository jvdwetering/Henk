import pickle

import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

class BaseGame(object):
    game_type = 0 #specifies which game it is. Should be unique for each class
    def __init__(self, bot, game_id, players, date):
        self.bot = bot
        self.game_id = game_id #unique identifier for this game instance
        self.is_active = True
        self.player_names = {}
        for user_id, user_name in players:
            self.player_names[user_id] = user_name
        self.date = date

        #self.current_users = [] # The list of user_ids for which the game is waiting for input.

        self.callbacks = [] #consists of tuples ((chat_id, message_id), callback) where callback is 
                            # a function with 2 arguments: ident, button_id where
                            # ident = (chat_id, message_id)
        self.save_game_state()


    def send_user_message(self, msg, user_id=None):
        '''Send msg to user_id. If user_id is None, it sends the message to all the players'''
        if user_id:
            self.bot.telebot.sendMessage(user_id, msg)
            return
        for i in self.player_names:
            self.bot.telebot.sendMessage(i, msg)


    def send_keyboard_message(self, chat_id, text, buttons, callback):
        options = []
        for i,o in enumerate(buttons):
            options.append(InlineKeyboardButton(text=o,callback_data="games%d:%d:%d" % (self.game_id,len(self.callbacks),i)))
        keyboard = InlineKeyboardMarkup(inline_keyboard=[options])
        sent = self.bot.telebot.sendMessage(chat_id, text, reply_markup=keyboard)
        ident = telepot.message_identifier(sent)
        self.callbacks.append((ident, callback))

    def disable_keyboard(self, ident):
        editor = telepot.helper.Editor(self.bot.telebot, ident)
        editor.editMessageReplyMarkup()
        self.bot.telebot.deleteMessage(ident)

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['bot']
        return state

    def save_game_state(self):
        self.bot.dataManager.add_game(self.game_type,self.game_id,pickle.dumps(self),self.date, self.is_active)