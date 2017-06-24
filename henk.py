#!/usr/bin/python3
# coding=latin-1
'''
Henkbot 2017
Should be run in at least Python 3.5 (3.4 maybe works as well)
Dependencies: telepot, simpleeval, dataset, textblob
Install these with "pip install libname" and for textblob additionally call python -m textblob.download_corpora

'''

import time
import random
import json
import urllib3

import simpleeval #for evaluating math expressions
simpleeval.MAX_POWER=1000
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InlineQueryResultArticle, InlineQueryResultPhoto, InputTextMessageContent

import get_wikipedia
from managedata import ManageData
import longstrings
from util import get_current_hour, normalise, startswith, probaccept

import math
math_constants = {"pi": math.pi, "e": math.e, "true": True, "false": False, "True": True, "False": False}
math_functions = {"sin": math.sin, "cos": math.cos, "sqrt": math.sqrt, "ln": math.log, "log": math.log10}


class Henk(object):
    def __init__(self):
        self.load_files()

        self.querycounts = {}
        self.lastupdate = 0
        self.active = False

    def load_files(self):
        f = open("grappen.txt","r",encoding='latin-1')
        self.jokes = f.read().splitlines()
        f.close()
        f = open("weetjes.txt","r",encoding='latin-1')
        self.facts = f.read().splitlines()
        f.close()
        f = open("zinnen.txt","r",encoding='latin-1')
        self.openinglines = f.read().splitlines()
        f.close()
        f = open("commands.json","r")
        d = json.load(f) #dictionary of lists of variations of commands and responses
        f.close()
        self.commands = d["commands"]
        self.responses = d["responses"]

        self.userresponses = dataManager.get_all_responses()
        for k,v in list(self.userresponses.items()):
            if k.startswith("$"):
                self.responses[k[1:]].extend(v)
                del self.userresponses[k]
        self.silentchats = dataManager.get_silent_chats()

    def sendMessage(self, chat_id, s):
        bot.sendMessage(chat_id, s)
        if probaccept(0.7): self.active = True
        else: self.active = False

    def pick(self, options):
        return random.sample(options,1)[0].replace("!name", self.sendername)

    def update_querycounts(self, amount):
        for q in self.querycounts:
            self.querycounts[q] = max([0,self.querycounts[q]-amount])

    def react_to_query(self, q):
        if q not in self.querycounts: self.querycounts[q] = 0
        if q.find("henk") != -1 or self.active:
            self.querycounts[q] += 1
            self.active = True
            return True
        if probaccept(2**-(max([self.querycounts[q]-1,0]))):
            self.querycounts[q] += 1
            self.active = True
            return True
        return False

    
                    

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type != 'text':
            print('Chat:', content_type, chat_type, chat_id)
            self.active = False
            return

        dataManager.write_message(msg)
        rawcommand = msg['text']
        command = normalise(msg['text'])
        try:
            print('Chat:', chat_type, chat_id, command)
        except UnicodeDecodeError:
            print('Chat:', chat_type, chat_id, command.encode('utf-8'))
        try:
            self.sender = msg['from']['id']
            self.sendername = msg['from']['first_name']
        except:
            self.sender = 0
            self.sendername = ""

        #serious stuff first

        if rawcommand.startswith("/help"):
            if chat_id in self.silentchats: bot.sendMessage(chat_id, longstrings.helpsilent)
            else: bot.sendMessage(chat_id, longstrings.helptext)
            return

        if rawcommand.startswith("/learnhelp"):
            bot.sendMessage(chat_id, longstrings.learnhelp)
            return
        
        if rawcommand.startswith('/say '):
            try:
                if self.sender == ADMIN:
                    bot.sendMessage(PPA, rawcommand[4:])
                    return
            except KeyError:
                return

        if rawcommand == "/reload":
            try:
                if self.sender == ADMIN:
                    self.load_files()
                    bot.sendMessage(chat_id, "reloading files")
                    return
            except KeyError:
                bot.sendMessage(chat_id, "I'm afraid I can't let you do that")
                return

        if rawcommand.startswith("/setsilent"):
            t = rawcommand[11:].strip()
            if not t.isdigit():
                bot.sendMessage(chat_id, "1 of 0 aub")
                return
            else:
                v = int(bool(int(t)))
                dataManager.set_silent_mode(chat_id, v)
                if v == 1 and not chat_id in self.silentchats:
                    self.silentchats.append(chat_id)
                if v == 0 and chat_id in self.silentchats:
                    self.silentchats.remove(chat_id)
                bot.sendMessage(chat_id, "done")
                return

        if rawcommand.startswith("/wiki"):
            text = rawcommand[6:]
            res = get_wikipedia.wiki_text(text)
            if res: bot.sendMessage(chat_id, res)
            else: bot.sendMessage(chat_id, "sorry, dat lukt me niet :(")
            return

        if rawcommand.startswith("/calc"):
            text = rawcommand[6:]
            bot.sendMessage(chat_id, self.response_math(text,clean=True))
            return

        if rawcommand.startswith("/stats"):
            text = self.response_stats(chat_id)
            bot.sendMessage(chat_id, text)
            return

        if rawcommand.startswith("/learnstats"):
            r = dataManager.get_all_responses()
            c = len(r)
            d = sum([len(i) for i in r.values()])
            bot.sendMessage(chat_id, "Ik ken %d custom queries, en heb daar in totaal %d responses op" % (c,d))
            return

        if rawcommand.startswith("/learn"):
            if rawcommand.find("->") == -1:
                bot.sendMessage(chat_id, "ik mis een '->' om aan te geven hoe de argumenten gescheiden zijn")
            call, response = rawcommand[7:].split("->",1)
            responses = [i.strip() for i in response.split("|") if i.strip()]
            if not responses:
                bot.sendMessage(chat_id, "geef geldige responses pl0x")
                return
            c = call.lower().strip().replace(", ", " ").replace("?","")
            if c in (self.commands["introductions"] + self.commands["funny"]
                     + self.commands["amuse"] + self.commands["spam_ask"]):
                bot.sendMessage(chat_id, "deze query mag niet (beschermd)")
                return
            if c.startswith("/"):
                bot.sendMessage(chat_id, "queries mogen niet beginnen met /")
                return
            if c.startswith("$"):
                if c[1:] not in self.responses.keys():
                    bot.sendMessage(chat_id, "geen geldig label")
                    return
                else: self.responses[c[1:]].extend(responses)
            dataManager.add_response(c, responses, self.sender, msg['date'])
            if not c.startswith("$"):
                if c in self.userresponses: self.userresponses[c].extend(responses)
                else: self.userresponses[c] = responses
            bot.sendMessage(chat_id, "ik denk dat ik het snap")
            return

        if rawcommand.startswith("/viewresponses"):
            r = dataManager.get_user_responses(self.sender)
            s = "Lijst van je geleerde commando's:"
            for i, d in enumerate(r):
                s += "\n%d.: %s -> %s" % (i, d[0], d[1])
            lines = s.splitlines()
            for i in range(0, len(lines), 15):
                bot.sendMessage(chat_id, "\n".join(lines[i:i+15]))
            return

        if rawcommand.startswith("/delete"):
            n = rawcommand[8:].strip()
            if not n.isdigit():
                bot.sendMessage(chat_id, "dat is geen geldig getal")
                return
            if dataManager.delete_response(self.sender, int(n)):
                self.load_files()
                bot.sendMessage(chat_id, "Gelukt!")
            else:
                bot.sendMessage(chat_id, "hmm, iets ging mis. Check even of het getal daadwerkelijk klopt")
            return
            
        if chat_id in self.silentchats:
            self.active = False
            return
        
        #now for the fun stuff :)

        #custom user commands
        c = rawcommand.lower().strip().replace(", "," ").replace("?","")
        if c in self.userresponses.keys():
            t = msg['date']
            if t-self.lastupdate > 600:
                self.update_querycounts(int((t-self.lastupdate)/3600))
                self.lastupdate = t
            if self.react_to_query(c):
                p = self.pick(self.userresponses[c])
                try: p = p.replace("!name", msg['from']['first_name'])
                except: pass
                if p: bot.sendMessage(chat_id, p)
                return
            
        #respond to cussing
        if startswith(command.replace(", "," "), self.commands['cuss_out']):
            self.sendMessage(chat_id, self.pick(self.responses['cuss_out']))
            return
        
        for i in self.commands['introductions']:
            if command.startswith(i):
                command = command[len(i)+1:].strip()
                break
        else:
            if not self.active: return #no introduction given and not active
        if command.startswith(","): command = command[1:].strip()
        if command.startswith("."): command = command[1:].strip()
        if not command: #only an introduction, no further text
            try:
                name = msg['from']['first_name']
                if name == "Olaf": name = "Slomp"
                val = self.pick(self.responses["hi"]).replace("!name",name)
                self.sendMessage(chat_id, val)
                return
            except KeyError:
                self.active = False
                return

        if command.startswith("wat kun je allemaal"):
            self.sendMessage(chat_id, longstrings.helptext)
            return

        if command.startswith("hoe kunnen we je helpen dingen te leren"):
            self.sendMessage(chat_id, longstrings.learnhelp)
            return

        #jokes
        val = startswith(command, self.commands["funny"])
        if val:
            s = self.pick(["Sure: ", "oké. ", ""])
            if probaccept(0.5):
                self.sendMessage(chat_id, s+self.pick(self.jokes))
            else:
                self.sendMessage(chat_id,self.pick(self.facts))
            return

        #facts
        val = startswith(command, self.commands["amuse"])
        if val:
            if probaccept(0.5):
                self.sendMessage(chat_id,self.pick(self.facts))
            else:
                s = get_wikipedia.random_wiki_text()
                if s: self.sendMessage(chat_id,s)
            return

        #spam check
        if startswith(command, self.commands["spam_ask"]):
            s = self.response_stats(chat_id)
            self.sendMessage(chat_id, s)
            return
        if startswith(command, self.commands["spam_react"]):
            self.sendMessage(chat_id, "spam"*random.randint(3,15))
            return
        
        #math
        val = startswith(command, self.commands["math"])
        if val:
            t = command[len(val)+1:].strip()
            if t.endswith("?"): t = t[:-1]
            self.sendMessage(chat_id, self.response_math(t))
            return
        
        #wiki question
        val = startswith(command, self.commands["question"])
        if val:
            if command.find("moeder")!=-1:
                self.sendMessage(chat_id, self.pick(self.responses["je_moeder"]))
                return
            i = rawcommand.find(val) # we need the original because capitalization is important
            if i == -1: t = command[len(val)+1:]#the question is capitalized or something, fall back
            else: t = rawcommand[i+len(val)+1:]
            t = t.replace("?","").replace("!","").replace(".","").replace('"',"").strip()
            res = get_wikipedia.wiki_text(t)
            if res: self.sendMessage(chat_id, res)
            else:
                if probaccept(0.5):
                    self.sendMessage(chat_id, self.pick(self.responses["wiki_failure"]))
                else: self.sendMessage(chat_id, self.pick(self.responses["negative_response"]))
            return
        
        #random reactions
        if len(command)>10:
            if command[-5:].find("?")!=-1:
                if command.find("hoeveel")!=-1 or command.find("hoe vaak")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_amount"]))
                elif command.find("waarom")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_why"]))
                elif command.find("wat vind")!=-1 or command.find("hoe denk")!=-1 or command.find("vind je")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_opinion"]))
                elif command.find("wat ")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_what"]))
                elif command.find("waar ")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_where"]))
                elif command.find("hoe ")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_how"]))
                elif command.find("wanneer")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_when"]))
                elif command.find("welk")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_which"]))
                elif command.find("wie")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_who"]))
                else:
                    self.sendMessage(chat_id, self.pick(self.responses["question_degree"]))
                return
            self.active = False
            if probaccept(0.05):
                bot.sendMessage(chat_id, self.pick(self.openinglines))
                return
            elif probaccept(0.2):
                bot.sendMessage(chat_id,self.pick(self.responses["negative_response"]))
            return

        self.active = False


    def on_callback_query(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        print('Callback query:', query_id, from_id, data)


    def on_inline_query(self, msg):
        def compute():
            query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
            result = []
            s = query_string.lower().strip()
            for k,v in longstrings.photos.items():
                if k.find(s)!=-1:
                    result.append(InlineQueryResultPhoto(id=k,photo_url=v,thumb_url=v))

            return result

        answerer.answer(msg, compute)


    def on_chosen_inline_result(self, msg):
        result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
        print('Chosen Inline Result:', result_id, from_id, query_string)

    def response_math(self, t, clean=False): #if not clean it outputs random error messages
        try:
            result = simpleeval.simple_eval(t.replace("^","**"),functions=math_functions, names=math_constants)
            if type(result) == bool:
                if result: result = "waar"
                else: result = "niet waar"
            return "Dat is " + str(result)
        except (simpleeval.InvalidExpression, simpleeval.FunctionNotDefined,
                simpleeval.AttributeDoesNotExist,KeyError):
            if not clean: return self.pick(self.commands["math_error"])
            else: return "Sorry, dat snap ik niet :("
        except simpleeval.NumberTooHigh:
            return "Sorry, dat is te moeilijk voor me"
        except Exception:
            return "computer says no"

    def response_stats(self, chat_id):
        total, topwords, p = dataManager.spam_stats(chat_id,hours=6)
        s = "Er zijn %d berichten verstuurd in de afgelopen 6 uur" % total
        s += "\nHardste spammers: "
        for i in range(min([len(p),3])):
            n, c = p[i][0], p[i][1]
            name = bot.getChatMember(chat_id, n)['user']['first_name']
            s += name + " (%d) " % c
        s += "\nMeest voorkomende woorden: %s" % ", ".join(topwords)
        return s



if __name__ == '__main__':

    f = open("apikey.txt", "r")
    TOKEN = f.read() #token for Henk
    f.close()

    #PPA = -6722364 #hardcoded label for party pownies
    PPA = -218118195 #Henk's fun palace

    ADMIN = 19620232 #John

    bot = telepot.Bot(TOKEN)
    answerer = telepot.helper.Answerer(bot)
    
    dataManager = ManageData()
    try: 
        henk = Henk()
        MessageLoop(bot, {'chat': henk.on_chat_message,
                          'callback_query': henk.on_callback_query,
                          'inline_query': henk.on_inline_query,
                          'chosen_inline_result': henk.on_chosen_inline_result}).run_as_thread()
        print('Listening ...')

        silent=False

        h = get_current_hour()
        if not silent:
            if h>6 and h<13:
                bot.sendMessage(PPA,"Goedemorgen")
            elif h>12 and h<19:
                bot.sendMessage(PPA,"Goedemiddag")
            else:
                bot.sendMessage(PPA,"Goedeavond")

        # Keep the program running.
        while True:
            try:
                time.sleep(1)
            except ConnectionResetError:
                print("ConnectionResetError")
            except urllib3.exceptions.ProtocolError:
                print("ProtocolError")
    except KeyboardInterrupt:
        pass
    finally:
        dataManager.close()
        bot.sendMessage(PPA,"Ik ga even slapen nu. doei doei")
