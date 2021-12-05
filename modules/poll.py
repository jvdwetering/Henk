#############################################################################
# THIS MODULE IS NO LONGER USED AS IT IS SUPERCEDED BY TELEGRAM'S OWN FEATURE
#############################################################################

import json

import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from .base import Module


class Poll(Module):
    def initialise(self, bot):
        self.polls = []
        self.pollvotes = []
        d = bot.dataManager.get_all_polls()
        for p in d:
            t = p['text'].split('|')
            self.polls.append(((p['chat_id'],p['mess_id']),t[0].strip(),t[1:]))
            self.pollvotes.append(json.loads(p['votes']))


    def register_commands(self, bot):
        bot.add_slash_command("poll", self.poll)
        bot.add_callback_query("poll", self.callback)

    def poll(self, bot, msg):
        text = msg.command
        d = text.split("|")
        if len(d) == 1:
            options = [u"\u2764", u"\U0001F4A9"] #heart and poop
        elif len(d)>6:
            return"Zoveel opties... omg, dat kan ik echt niet aan"
        else:
            options = [i.strip()[:15] for i in d[1:]]
        query = d[0].strip()
        buttons = []
        for i,o in enumerate(options):
            buttons.append(InlineKeyboardButton(text=o,callback_data="poll%d:%d" % (len(self.polls),i)))
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        sent = bot.telebot.sendMessage(msg.chat_id, "Poll: %s" % query, reply_markup=keyboard)
        ident = telepot.message_identifier(sent)
        bot.dataManager.add_poll(ident[0],ident[1],len(self.polls),query+"|"+"|".join(options),"{}")
        self.polls.append((ident, query, options))
        self.pollvotes.append({})
        return

    def callback(self, bot, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        poll, option = data[4:].split(":")
        poll = int(poll)
        option = int(option)
        if str(from_id) in self.pollvotes[poll] and self.pollvotes[poll][str(from_id)] == option: return
        self.pollvotes[poll][str(from_id)] = option

        p = self.polls[poll]
        bot.dataManager.add_poll(p[0][0],p[0][1], poll, p[1]+"|"+"|".join(p[2]), json.dumps(self.pollvotes[poll]))
        
        editor = telepot.helper.Editor(bot.telebot, self.polls[poll][0])
        buttons = []
        for i,o in enumerate(self.polls[poll][2]):
            c = sum(1 for k,v in self.pollvotes[poll].items() if v==i)
            if c == 0: s = o
            else: s = "%s %d" % (o, c)
            buttons.append(InlineKeyboardButton(text=s,callback_data="poll%d:%d" % (poll,i)))
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        editor.editMessageReplyMarkup(reply_markup=keyboard)
        bot.telebot.answerCallbackQuery(query_id, text="Je hebt gestemd op " + p[2][option])
        return

poll = Poll()