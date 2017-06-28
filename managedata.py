import time
import zlib
import math
import os

import dataset
from textblob import TextBlob

from subprocess import call
try:
    f = open("password.txt", "r")
except:
    raise Exception("Password file not found")
password = f.read().strip()
f.close()

def encrypt():
    call(r"openssl enc -aes-256-cbc -salt -in data.db -out data.db.enc -pass pass:"+password,
         shell=True)

def decrypt():
    call(r"openssl enc -d -aes-256-cbc -salt -in data.db.enc -out data.db -pass pass:"+password,
         shell=True)


PPA = -6722364 #hardcoded label for party pownies
PPA = -218118195 #Henk's fun palace

wordfilterlist = [
    "komt", "omdat", "niet", "eens", "moet", "maar", "learn", "viewresponses",
    "gaan", "nice", "doen", "heeft", "iets","over", "naar", "veel", "daar",
    "voor", "henk", "welke", "waarom", "vind", "zijn", "echt", "mijn", "delete",
    "gaat", "goed", "denk", "meer", "bent", "waar", "weer", "toch", "even"]

def is_word_relevant(word):
    if len(word) < 4: return False
    if word.isdigit(): return False
    if word in wordfilterlist: return False
    return True

class ManageData(object):
    def __init__(self):
        f = open("isencrypted.txt", "r")
        val = int(f.read())
        if val:
            decrypt()
            time.sleep(0.3)
            f = open("isencrypted.txt", "w")
            f.write("0")
            f.close()
        else:
            print("Database wasn't encrypted on last closure")
        self.db = dataset.connect('sqlite:///data.db?check_same_thread=False')
        self.messages = self.db['Messages']
        self.users = self.db['Users']
        self.commands = self.db['Commands']
        self.aliases = self.db['Aliases']
        self.chats = self.db['Chats']
        self.polls = self.db['Polls']
        self.dummy = False

        self.alltext = "\n".join(i['text'] for i in self.messages.all())

    def close(self):
        print(os.getcwd())
        encrypt()
        f = open("isencrypted.txt", "w")
        f.write("1")
        f.close()

    def write_message(self, msg):
        if self.dummy: return
        d = {'chat_id': msg['chat']['id'], 'chat_type': msg['chat']['type'],
             'from_id': msg['from']['id'], 'from_name': msg['from']['first_name'],
             'time': msg['date'], 'text': msg['text']}
        self.alltext += "\n" + d['text']
        self.messages.insert(d)

    def latest_messages(self, chat_id, hours=3):
        begin = int(time.time() - hours*3600)
        res = self.db.query("SELECT time, from_id, text FROM Messages WHERE (chat_id = %d) AND (time >= %d) ORDER BY time" % (chat_id, begin))

        return res

    def spam_stats(self, chat_id, hours=3):
        msgs = self.latest_messages(chat_id,hours)
        count = {}
        t = 0
        totaltext = ""
        for m in msgs:
            i = m['from_id']
            if i in count:
                count[i] += 1
            else: count[i] = 1
            t += 1
            totaltext += "\n" + m['text']
        b1 = TextBlob(totaltext)
        words = dict(b1.word_counts)
        words = filter(lambda x: is_word_relevant(x[0]), words.items())
        words = [i[0] for i in sorted(words, key=lambda x: x[1], reverse=True)]
        topposters = sorted(count.items(), key=lambda x: x[1], reverse=True)[:3]
        char_words = [d[0] for d in top_words(b1, TextBlob(self.alltext))]
        return (t, words[:10], topposters, char_words[:10])

    def add_response(self, call, responses, user_id, time):
        if self.dummy: return
        self.commands.insert({'user_id': user_id, 'call': call, 'response': " | ".join(responses), "time": time})

    def get_all_responses(self):
        com = self.commands.all()
        cdict = {}
        for c in com:
            r = c['response'].split(" | ")
            if c['call'] in cdict:
                cdict[c['call']].extend(r)
            else: cdict[c['call']] = r

        return cdict

    def get_user_responses(self, user):
        com = self.commands.find(user_id = user, order_by='time')
        return [(c['call'], c['response']) for c in com]

    def delete_response(self, user, num):
        if self.dummy: return
        res = self.get_user_responses(user)
        if num >= len(res): return False
        self.commands.delete(user_id=user, call=res[num][0], response=res[num][1])
        return True

    def add_alias(self, aliases, user_id, time):
        if self.dummy: return
        self.aliases.insert({'user_id': user_id, 'aliases': " | ".join(aliases), 'time': time})

    def get_all_aliases(self):
        com = self.aliases.all()
        return [c['aliases'].split(" | ") for c in com]

    def get_user_aliases(self, user):
        com = self.aliases.find(user_id = user, order_by='time')
        return [c['aliases'] for c in com]

    def delete_alias(self, user, num):
        if self.dummy: return
        res = self.get_user_aliases(user)
        if num >= len(res): return False
        self.aliases.delete(user_id=user, aliases=res[num])
        return True

    def add_poll(self, chat_id, mess_id, poll_id, text, votes):
        if self.dummy: return
        d = {'chat_id': chat_id, 'mess_id': mess_id, 'poll_id': poll_id, 'text': text, 'votes': votes}
        if self.polls.find_one(chat_id=chat_id,mess_id=mess_id):
            self.polls.update(d, ['chat_id', 'mess_id'])
        else:
            self.polls.insert(d)

    def get_all_polls(self):
        return self.polls.find(order_by='poll_id')

    def set_silent_mode(self, chat_id, setsilent):
        if self.dummy: return
        if self.chats.find_one(chat_id = chat_id):
            self.chats.update({"chat_id": chat_id, "silent":setsilent}, ['chat_id'])
        else:
            self.chats.insert({"chat_id": chat_id, "silent":setsilent})

    def get_silent_chats(self):
        t = self.chats.find(silent=1)
        return [i['chat_id'] for i in t]
        

def tf(word, blob):
    return (blob.words.count(word)+1) / len(blob.words)

def n_containing(word, bloblist):
    return sum(1 for blob in bloblist if word in blob.words)

def idf(word, bloblist):
    return math.log(len(bloblist) / (1 + n_containing(word, bloblist)))

def tfidf(word, blob, bloblist):
    return tf(word, blob) * idf(word, bloblist)

def comp_freq(word, blob1, blob2):
    return tf(word,blob1)/tf(word,blob2)

def top_words(blob1,blob2):
    l = [(w,blob1.word_counts[w]/(1+blob2.word_counts[w])) for w in blob1.word_counts if blob1.word_counts[w]>3 and is_word_relevant(w)]
    return sorted(l, key=lambda x: x[1],reverse=True)

if __name__ == '__main__':
    m = ManageData()
    data = m.db['Messages'].all()
    totaltext = "\n".join(i['text'] for i in data)
    b1 = TextBlob(totaltext)
    data = m.latest_messages(PPA, 24)
    t = "\n".join(i['text'] for i in data)
    b2 =TextBlob(t)
