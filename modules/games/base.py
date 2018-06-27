import pickle

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

        #self.current_users = [] # The list of user_ids for which the game is waiting for input.

        self.callbacks = [] #consists of tuples ((chat_id, message_id), callback) where callback is 
                            # a function with 2 arguments: ident, button_id where
                            # ident = (chat_id, message_id)

        self.final_callback = None
        self.save_game_state()

    def game_ended(self):
        self.is_active = False
        if self.final_callback: self.final_callback(self)


    def send_user_message(self, msg, user_id=None):
        '''Send msg to user_id. If user_id is None, it sends the message to all the players'''
        if user_id:
            self.bot.telebot.sendMessage(user_id, msg)
            return
        for i in self.player_names:
            self.bot.telebot.sendMessage(i, msg)

    def get_keyboard(self, buttons, index):
        options = []
        for i,o in enumerate(buttons):
            options.append(InlineKeyboardButton(text=o,callback_data="games%d:%d:%d" % (self.game_id,index,i)))
        return InlineKeyboardMarkup(inline_keyboard=[options])

    def send_keyboard_message(self, chat_id, text, buttons, callback):
        keyboard = self.get_keyboard(buttons, len(self.callbacks))
        sent = self.bot.telebot.sendMessage(chat_id, text, reply_markup=keyboard)
        ident = telepot.message_identifier(sent)
        self.callbacks.append((ident, callback))
        return ident

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


def gamestarter(parent, bot, index, gameclass, maxplayers, sender, chat, welcome, cmd):
    options = []
    buttons = ["join/unjoin", "start"]
    for i,o in enumerate(buttons):
        options.append(InlineKeyboardButton(text=o,callback_data="gamestart{}:{}".format(str(index),str(i))))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[options])
    sent = bot.telebot.sendMessage(chat, welcome+"\n*"+sender[1], reply_markup=keyboard)
    ident = telepot.message_identifier(sent)
    return StartManager(parent, bot, gameclass, maxplayers, sender, ident, keyboard, welcome, cmd)

class BaseDispatcher(BaseGame):
    def __init__(self, bot, game_id, msg):
        super().__init__(bot, game_id, [], msg.date, msg.command)
        self.chat_id = msg.chat_id
        self.sender_id = msg.sender
        self.sender_name = msg.sendername
        self.message_init()

    def message_init(self):
        raise NotImplementedError("message_init not implemented")

    # def __init__(self, parent, bot, gameclass, maxplayers, sender, ident, keyboard, welcome, cmd):
    #     self.parent = parent
    #     self.bot = bot
    #     self.gameclass = gameclass
    #     self.maxplayers = maxplayers
    #     self.senderid = sender[0]
    #     self.sendername = sender[1]
    #     self.players = [(sender[0], sender[1])]
    #     self.ident = ident
    #     self.keyboard = keyboard
    #     self.welcome = welcome
    #     self.cmd = cmd

    #     self.active = True

    # def callback(self, button_id, sender, sendername,date):
    #     if not self.active: return
    #     if button_id == 0: #join/unjoin
    #         if self.players.count((sender,sendername)):
    #             self.players.remove((sender,sendername))
    #         else:
    #             if len(self.players) == self.maxplayers:
    #                 return "Het spel zit al vol"
    #             self.players.append((sender,sendername))
    #         self.update_message()
    #     elif button_id == 1: #start game
    #         if not self.players:
    #             return "Er moet wel iemand meedoen"
    #         if sender != self.senderid:
    #         	return "Alleen {} kan dit potje beginnen".format(self.sendername)
    #         index = len(self.bot.dataManager.games)
    #         self.active = False
    #         g = self.gameclass(self.bot,index,self.players,date, self.cmd)
    #         self.parent.games[index] = g
    #         editor = telepot.helper.Editor(self.bot.telebot, self.ident)
    #         editor.editMessageReplyMarkup()


    # def update_message(self):
    #     msg = self.welcome +"\n*" +"\n*".join(n for i, n in self.players)
    #     editor = telepot.helper.Editor(self.bot.telebot, self.ident)
    #     editor.editMessageText(msg, reply_markup=self.keyboard)