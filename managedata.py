import time
import math
import os
import pickle
import threading

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
KLAVERJAS_GROUP = -311240489

wordfilterlist = [
    "komt", "omdat", "niet", "eens", "moet", "maar", "learn", "viewresponses","showalias",
    "gaan", "nice", "doen", "heeft", "iets","over", "naar", "veel", "daar","alias","myresponses",
    "voor", "henk", "welke", "waarom", "vind", "zijn", "echt", "mijn", "delete","myaliases","deleteresponse",
    "gaat", "goed", "denk", "meer", "bent", "waar", "weer", "toch", "even", "stats"]

def is_word_relevant(word):
    if len(word) < 4: return False
    if word.isdigit(): return False
    if word in wordfilterlist: return False
    return True

class ManageData(object):
    def __init__(self):
        f = open("isencrypted.txt", "r")
        val = int(f.read())
        f.close()
        if val:
            decrypt()
            time.sleep(0.5)
            f = open("isencrypted.txt", "w")
            f.write("0")
            f.close()
        else:
            print("Database wasn't encrypted on last closure, encrypting now...")
            encrypt()
            time.sleep(0.5)
            print("decrypting...")
            decrypt()
            time.sleep(0.5)

        self.db = dataset.connect('sqlite:///data.db?check_same_thread=False')
        self.messages = self.db['Messages']
        self.users = self.db['Users']
        self.commands = self.db['Commands']
        self.aliases = self.db['Aliases']
        self.chats = self.db['Chats']
        self.polls = self.db['Polls']  # TODO: This feature is no longer needed, so we can remove it.
        self.games = self.db['Games']
        self.maxgameid = next(self.db.query("SELECT MAX(game_id) as max_id FROM Games;"))['max_id']
        self.klaverjas_results = self.db['KlaverjasResults']
        self.dummy = False
        self.datalock = threading.Lock()

        # self.alltext = "\n".join(i['text'] for i in self.messages.all())
        recentish_messages = self.db.query("SELECT text FROM Messages WHERE (time >= %d) ORDER BY time" % int(time.time() - 90*24*3600))
        self.alltext = "\n".join(i['text'] for i in recentish_messages)

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
        with self.datalock: self.messages.insert(d)

    def latest_messages(self, chat_id, hours=3):
        begin = int(time.time() - hours*3600)
        with self.datalock: res = self.db.query("SELECT time, from_id, text FROM Messages WHERE (chat_id = %d) AND (time >= %d) ORDER BY time" % (chat_id, begin))

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
        with self.datalock: self.commands.insert({'user_id': user_id, 'call': call, 'response': " | ".join(responses), "time": time})

    def get_all_responses(self):
        cdict = {}
        with self.datalock:
            com = self.commands.all()
            for c in com:
                r = c['response'].split(" | ")
                if c['call'] in cdict:
                    cdict[c['call']].extend(r)
                else: cdict[c['call']] = r

        return cdict

    def get_user_responses(self, user):
        with self.datalock: com = self.commands.find(user_id = user, order_by='time')
        return [(c['call'], c['response']) for c in com]

    def delete_response(self, user, num):
        if self.dummy: return
        res = self.get_user_responses(user)
        if num >= len(res): return False
        with self.datalock: self.commands.delete(user_id=user, call=res[num][0], response=res[num][1])
        return True


    def add_alias(self, aliases, user_id, time):
        if self.dummy: return
        with self.datalock: self.aliases.insert({'user_id': user_id, 'aliases': " | ".join(aliases), 'time': time})

    def get_all_aliases(self):
        with self.datalock:
            com = self.aliases.all()
            return [c['aliases'].split(" | ") for c in com]

    def get_user_aliases(self, user):
        with self.datalock:
            com = self.aliases.find(user_id = user, order_by='time')
            return [c['aliases'] for c in com]

    def delete_alias(self, user, num):
        if self.dummy: return
        res = self.get_user_aliases(user)
        if num >= len(res): return False
        with self.datalock: self.aliases.delete(user_id=user, aliases=res[num])
        return True


    def add_poll(self, chat_id, mess_id, poll_id, text, votes):
        if self.dummy: return
        d = {'chat_id': chat_id, 'mess_id': mess_id, 'poll_id': poll_id, 'text': text, 'votes': votes}
        with self.datalock:
            if self.polls.find_one(chat_id=chat_id,mess_id=mess_id):
                self.polls.update(d, ['chat_id', 'mess_id'])
            else:
                self.polls.insert(d)

    def get_all_polls(self):
        with self.datalock: return self.polls.find(order_by='poll_id')


    def add_game(self, game_type, game_id, game_data, date, is_active):
        if self.dummy: return
        d = {'game_type': game_type, 'game_id': game_id,
             'game_data': game_data, 'date': date, 'is_active': is_active}
        with self.datalock:
            if self.games.find_one(game_id=game_id):
                self.games.update(d, ['game_id'])
            else:
                self.maxgameid += 1
                self.games.insert(d)

    def get_unique_game_id(self):
        with self.datalock:
            self.maxgameid += 1
            return self.maxgameid

    def get_active_games(self, game_type=None):
        with self.datalock:
            if not game_type:
                return self.games.find(is_active=True, order_by='game_id')
            return self.games.find(game_type=game_type, is_active=True, order_by='game_id')

    def load_game(self, game_id):
        with self.datalock:
            g = self.games.find_one(game_id=game_id)
            return pickle.loads(g['game_data'])


    def add_klaverjas_result(self, seed, game_id, result):
        if self.dummy: return
        d = {'seed': seed, 'game_id': game_id, 'result': result}
        with self.datalock:
            if self.klaverjas_results.find_one(game_id=game_id):
                self.klaverjas_results.update(d, ['game_id'])
            else:
                self.klaverjas_results.insert(d)

    def set_silent_mode(self, chat_id, setsilent):
        if self.dummy: return
        with self.datalock:
            if self.chats.find_one(chat_id = chat_id):
                self.chats.update({"chat_id": chat_id, "silent":setsilent}, ['chat_id'])
            else:
                self.chats.insert({"chat_id": chat_id, "silent":setsilent})

    def get_silent_chats(self):
        with self.datalock:
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

from unidecode import unidecode

translate_name = {
    "@john": "John",
    "@jvdwetering": "John",
    "@memecardsbot": "Henk",
    "@olafz": "Olaf",
    "@DanyTargaryen": "Margot",
    "@jesper216": "Jesper",
    "@vetkat": "Mark",
    "@mark": "Mark",
    "@Alucen": "Alex",
    "@koemanmike": "Mike",
    "@riiik": "Rik",
    "@rik": "Rik"
    }

def cleanup_msg(text):
    t = unidecode(str(text))
    #for c in r"+-_;{}[](),.!|\&?/%:<>=#*~^`$":
    #    t = t.replace(c," ")
    #t = t.replace("'",'"')
    #for c in "0123456789":
    #    t = t.replace(c,"#")
    if t.startswith("/"):
        return ""
    for k,v in translate_name.items(): #"filter out @callsigns"
        t = t.replace(k,v)
    while t.find("http")!=-1: #filter out urls
        i = t.find("http")
        j = t.find(" ",i)
        if j==-1: t = t[:i]
        else: t = t[:i] + t[j:]
    t = t.strip()
    t = "\n".join([" ".join(line.split()) for line in t.split("\n")]) #normalise spaces
    return t

def linesplit(line, sep):
    #linesplit("Even testen of dit werkt\nWerkt het??\n Misschien wel", ["\n","?"])
    # = ['Even testen of dit werkt', 'Werkt het?', 'Misschien wel']
    l = [line]
    for s in sep:
        l2 = []
        for i in l:
            splits = i.split(s)
            for i in range(len(splits)-1): splits[i] += s
            l2.extend(j.strip() for j in splits if len(j.strip())>1)
        l = l2
    return l

def prepare_pownies_text(m):
    msgs = [i['text'] for i in m.messages.find(chat_id = -6722364)]
    print(len(msgs), "amount of messages")
    texts = []
    for t in list(filter(lambda x: x!="", [cleanup_msg(msg) for msg in msgs])):
        l = linesplit(t, ["\n","? ",". ", "! "])
        texts.extend(l)

    print("Split into", len(texts), "amount of lines")
    b = [i for i in texts if any(i.find(name)!=-1 for name in translate_name.values())]
    print(len(b), "contain names")
    c = [i for i in texts if any(i.find(d)!=-1 for d in "0123456789")]
    print(len(c), "contain a number")
    return texts


    
##
##if __name__ == '__main__':
##    m = ManageData()
##    data = m.db['Messages'].all()
##    totaltext = "\n".join(i['text'] for i in data)
##    b1 = TextBlob(totaltext)
##    data = m.latest_messages(PPA, 24)
##    t = "\n".join(i['text'] for i in data)
##    b2 =TextBlob(t)
