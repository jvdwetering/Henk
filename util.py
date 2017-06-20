import datetime
import random
import re

def get_current_hour():
    return datetime.datetime.time(datetime.datetime.now()).hour

remove_emoji = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)

def normalise(s): #"Hoi   bla" -> "hoi bla"
    r = s.lower().strip()
    r = remove_emoji.sub('', r)
    r = " ".join(r.split())
    return r

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
