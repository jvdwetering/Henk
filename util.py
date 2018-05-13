import datetime
import random
import re
import os

import telepot

datadir = os.path.abspath("datafiles")
print(datadir)

def get_current_hour():
    return datetime.datetime.time(datetime.datetime.now()).hour

remove_emoji = re.compile(u'['
     u'\U0001F300-\U0001F64F'
     u'\U0001F680-\U0001F6FF'
     u'\u2600-\u26FF\u2700-\u27BF]+', 
     re.UNICODE)

def normalise(s): #" Hoi   bla" -> "hoi bla"
    r = s.lower().strip()
    r = remove_emoji.sub('', r)
    r = " ".join(r.split())
    return r

def prepare_query(s):
    r = s.lower().strip().replace(", "," ").replace("?","").replace("!","")
    if r.endswith("."): r = r[:-1]
    return r.strip()

def startswith(s,l):
    for i in l:
        if s.startswith(i):
            return i
    return False

def pick(l): #picks random element from list
    return random.sample(l,1)[0]

def probaccept(p): #returns True with probability p, otherwise False
    if random.random() < p:
        return True
    return False

class Message(object):
    def __init__(self,msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        self.content_type = content_type
        self.istext = (content_type == 'text')
        self.chat_id = chat_id
        self.chat_type = chat_type
        if self.istext:
            self.raw = msg['text']
            self.normalised = normalise(msg['text'])
            self.command = self.normalised
        else:
            self.raw = ""
            self.normalised = ""
            self.command = ""
        try:
            self.sender = msg['from']['id']
            self.sendername = msg['from']['first_name']
        except:
            self.sender = 0
            self.sendername = ""
        self.date = msg["date"]

        self.object = msg
