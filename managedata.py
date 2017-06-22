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
password = f.read()
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
    "dat", "wel", "het", "hoi", "jij",
    "wil", "dit", "komt", "als", "kan", "ook", "bij"
    "omdat", "een", "wat", "niet", "met", "eens", "moet",
    "van", "ben", "heb", "voor", "henk", "welke", "hoe", "waarom",
    "die", "vind", "dan", "zijn", "zou", "hij", "aan", "nog"]

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
        self.chats = self.db['Chats']

    def close(self):
        print(os.getcwd())
        encrypt()
        f = open("isencrypted.txt", "w")
        f.write("1")
        f.close()

    def write_message(self, msg):
        d = {'chat_id': msg['chat']['id'], 'chat_type': msg['chat']['type'],
             'from_id': msg['from']['id'], 'from_name': msg['from']['first_name'],
             'time': msg['date'], 'text': msg['text']}
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
        #ratio = len(zlib.compress(totaltext.encode(),level=9))/len(totaltext)
        words = dict(TextBlob(totaltext).word_counts)
        words = filter(lambda x: len(x[0])>2 and x[0] not in wordfilterlist, words.items())
        words = [i[0] for i in sorted(words, key=lambda x: x[1], reverse=True)]
        topposters = sorted(count.items(), key=lambda x: x[1], reverse=True)[:3]
        return (t, words[:10], topposters)

    def add_response(self, call, responses, user_id, time):
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
        res = self.get_user_responses(user)
        if num > len(res): return False
        self.commands.delete(user_id=user, call=res[num][0], response=res[num][1])
        return True

    def set_silent_mode(self, chat_id, setsilent):
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
    return sorted(blob1.words, key=lambda x: comp_freq(x,blob1,blob2),reverse=True)

if __name__ == '__main__':
    m = ManageData()
    data = m.db['Messages'].all()
    totaltext = "\n".join(i['text'] for i in data)
    b1 = TextBlob(totaltext)
    data = m.latest_messages(PPA, 24)
    t = "\n".join(i['text'] for i in data)
    b2 =TextBlob(t)
