import pickle
import threading

import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

class BaseGame(object):
    game_type = 0 #specifies which game it is. Should be unique for each class
    def __init__(self, bot, game_id, players, date, cmd=""):
        self.bot = bot
        self.game_id = game_id #unique identifier for this game instance
        self.is_active = True
        self.player_names = {}
        for user_id, user_name in players:
            self.player_names[user_id] = user_name
        self.date = date
        self.cmd = cmd
        self.loaded = False

        #self.current_users = [] # The list of user_ids for which the game is waiting for input.

        self.callbacks = [] #consists of tuples ((chat_id, message_id), callback) where callback is 
                            # a function with 2 arguments: ident, button_id where
                            # ident = (chat_id, message_id)

        self.final_callback = None

        self._lock = bot.messagelock
        #self.save_game_state()

    def load(self):
        self.loaded = True

    def game_ended(self):
        self.is_active = False
        if self.final_callback: self.final_callback(self)


    def send_user_message(self, msg, user_id=None, parse_mode=None):
        '''Send msg to user_id. If user_id is None, it sends the message to all the players'''
        with self._lock:
            if user_id:
                if not parse_mode: sent = self.bot.telebot.sendMessage(user_id, msg)
                else: sent = self.bot.telebot.sendMessage(user_id, msg, parse_mode=parse_mode)
                return telepot.message_identifier(sent)
            idents = []
            for i in self.player_names:
                if not parse_mode: sent = self.bot.telebot.sendMessage(i, msg)
                else: sent = self.bot.telebot.sendMessage(i, msg, parse_mode=parse_mode)
                idents.append(telepot.message_identifier(sent))
            return idents

    def edit_message_text(self, ident, msg, parse_mode=None):
        editor = telepot.helper.Editor(self.bot.telebot, ident)
        with self._lock:
            try:
                if parse_mode: editor.editMessageText(msg, parse_mode=parse_mode)
                else: editor.editMessageText(msg)
            except telepot.exception.TelegramError:
                pass

    def get_keyboard(self, buttons, index):
        options = []
        for i,o in enumerate(buttons):
            options.append(InlineKeyboardButton(text=o,callback_data="games%d:%d:%d" % (self.game_id,index,i)))
        return InlineKeyboardMarkup(inline_keyboard=[options])

    def send_keyboard_message(self, chat_id, text, buttons, callback):
        keyboard = self.get_keyboard(buttons, len(self.callbacks))
        with self._lock:
            sent = self.bot.telebot.sendMessage(chat_id, text, reply_markup=keyboard)
        ident = telepot.message_identifier(sent)
        self.callbacks.append((ident, callback))
        return ident

    def disable_keyboard(self, ident):
        editor = telepot.helper.Editor(self.bot.telebot, ident)
        with self._lock:
            editor.editMessageReplyMarkup()
            self.bot.telebot.deleteMessage(ident)

    def __getstate__(self):
        state = self.__dict__.copy()
        try: del state['bot']
        except KeyError: pass
        try: del state['_lock']
        except KeyError: pass
        return state

    def setstate(self, bot):
        self.bot = bot
        self._lock = bot.messagelock

    def save_game_state(self):
        with self._lock:
            self.bot.dataManager.add_game(self.game_type,self.game_id,pickle.dumps(self),self.date, self.is_active)


class BaseDispatcher(BaseGame):
    def __init__(self, bot, game_id, msg):
        super().__init__(bot, game_id, [], msg.date, msg.command)
        self.chat_id = msg.chat_id
        self.sender_id = msg.sender
        self.sender_name = msg.sendername
        self.message_init()

    def message_init(self):
        raise NotImplementedError("message_init not implemented")