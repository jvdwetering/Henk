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

telepot.glance = dummy_glance

henk.bot = Bot()
henk.dataManager = ManageData()
henk.dataManager.dummy = True
henkBot = henk.Henk()

while True:
    s = input(">>> ")
    henkBot.on_chat_message(make_message(s))
