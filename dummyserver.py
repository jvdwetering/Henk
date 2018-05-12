import time

import telepot

import henk
from managedata import ManageData

ADMIN = 19620232 #John
PPA = -218118195 #Henk's fun palace

class Bot(object):
    def sendMessage(self, chat_id, message):
        print(message)

    def getChatMember(self, chat_id, num):
        return {'user': {'first_name': 'iemand'}}

def dummy_glance(msg):
    return ('text', 'group', ADMIN)

def make_message(s):
    return {'text': s, 'from': {'id': ADMIN, 'first_name': 'John'},
            'date': int(time.time()),'chat':{'id':PPA}}

def alias_list():
    h = henkBot
    pairs = h.aliasdict.items()

    categories = []
    responses = []
    mix = []
    for i in set(h.aliasdict.values()):
        categories.append([k for k,v in pairs if v==i])
        responses.append(h.userresponses.get(i,[]))

        mix.append((categories[-1],responses[-1]))
        
    return mix, categories, responses


telepot.glance = dummy_glance

telebot = Bot()
henkBot = henk.Henk(telebot, isdummy=True)

while True:
    s = input(">>> ")
    henkBot.on_chat_message(make_message(s))
