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

import difflib

import simpleeval #for evaluating math expressions
simpleeval.MAX_POWER=1000
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InlineQueryResultArticle, InlineQueryResultPhoto, InputTextMessageContent

import get_wikipedia
from managedata import ManageData
from buienradar import weather_report
from entertainment import Entertainment
import reftermenu
import longstrings
from util import get_current_hour, normalise, prepare_query, startswith, probaccept

import math
math_constants = {"pi": math.pi, "e": math.e, "true": True, "false": False, "True": True, "False": False}
math_functions = {"sin": math.sin, "cos": math.cos, "sqrt": math.sqrt, "ln": math.log, "log": math.log10}


class Henk(object):
    def __init__(self):
        self.querycounts = {}
        self.lastupdate = 0
        self.active = False
        self.entertainment = Entertainment()
        self.morning_message_timer = 0

        self.polls = []
        self.pollvotes = []

        self.load_files()

    def load_files(self):
        self.entertainment.load()
        f = open("commands.json","r")
        d = json.load(f) #dictionary of lists of variations of commands and responses
        f.close()
        self.commands = d["commands"]
        self.responses = d["responses"]

        aliases = dataManager.get_all_aliases()
        self.aliasdict = {} #mapping a query to an int
        i = 0
        for synonyms in aliases: #go trough all lists of aliases
            for query in self.aliasdict: #for all registered aliases
                if query in synonyms: #check if it is in this list
                    for s in synonyms: #and then register them as the same
                        self.aliasdict[s] = self.aliasdict[query]
                    break
            else: #if not in the registered list
                for s in synonyms: #register them as a new subset
                    self.aliasdict[s] = i
                i += 1

        d = dataManager.get_all_responses()
        for k,v in list(d.items()):
            if k.startswith("$"): #special queries such as $question_what
                self.responses[k[1:]].extend(v)
                del d[k]

        self.userresponses = {} #mapping an int (from aliases) to a list of responses
        for query in d:
            if query in self.aliasdict:
                if self.aliasdict[query] in self.userresponses:
                    self.userresponses[self.aliasdict[query]].extend(d[query])
                else: self.userresponses[self.aliasdict[query]] = d[query]
            else:
                self.aliasdict[query] = i
                self.userresponses[i] = d[query]
                i += 1

        d = dataManager.get_all_polls()
        for p in d:
            t = p['text'].split('|')
            self.polls.append(((p['chat_id'],p['mess_id']),t[0].strip(),t[1:]))
            self.pollvotes.append(json.loads(p['votes']))
        
        self.silentchats = dataManager.get_silent_chats()

    def sendMessage(self, chat_id, s):
        m = bot.sendMessage(chat_id, s)
        if probaccept(0.7): self.active = True
        else: self.active = False
        return m

    def pick(self, options):
        return random.sample(options,1)[0].replace("!name", self.sendername)

    def update_querycounts(self, amount):
        for q in self.querycounts:
            self.querycounts[q] = max([0,self.querycounts[q]-amount])

    def react_to_query(self, q):
        i = self.aliasdict[q]
        if i not in self.querycounts: self.querycounts[i] = 0
        if (q.find("henk") != -1 or (self.active and probaccept(2**-(max([self.querycounts[i]-3,0]))))
            or probaccept(2**-(max([self.querycounts[i]-1,0])))):
            self.querycounts[i] += 1
            self.active = True
            return True
        return False

    def morning_message(self,chat_id, msg):
        if probaccept(0.3):
            if msg.startswith('/') and msg.find('morgen')!=-1:
                self.sendMessage(chat_id, msg)
            elif msg.find('morgen'): self.sendMessage(chat_id, msg)
            else: self.sendMessage(chat_id,"Goedemorgen")
            time.sleep(2.0)
            if probaccept(0.5):
                return weather_report()
            elif probaccept(0.5):
                return self.entertainment.get_sonnet()
            elif probaccept(0.5):
                return self.entertainment.get_joke()
            else:
                return self.entertainment.get_openingline()
            
        else:
            return None

       

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

        if rawcommand.startswith("/weather"):
            self.sendMessage(chat_id, weather_report())

        if rawcommand.startswith("/refter"):
            self.sendMessage(chat_id, reftermenu.get_todays_menu())

        if rawcommand.startswith("/calc"):
            text = rawcommand[6:]
            self.sendMessage(chat_id, self.response_math(text,clean=True))
            return

        if rawcommand.startswith("/stats"):
            m = self.sendMessage(chat_id, "effe tellen")
            text = self.response_stats(chat_id)
            bot.editMessageText(telepot.message_identifier(m), text)
            #bot.sendMessage(chat_id, text)
            return

        if rawcommand.startswith("/learnstats"):
            r = dataManager.get_all_responses()
            c = len(r)
            d = sum([len(i) for i in r.values()])
            a = dataManager.get_all_aliases()
            aa = sum([len(i) for i in a])
            self.sendMessage(chat_id, "Ik ken %d custom queries, en heb daar in totaal %d responses op. Verder ken ik %d aliases" % (c,d, aa))
            return

        if rawcommand.startswith("/poll"):
            text = rawcommand[6:]
            d = text.split("|")
            if len(d) == 1:
                options = [u"\u2764", u"\U0001F4A9"] #heart and poop
            elif len(d)>6:
                bot.sendMessage(chat_id, "Zoveel opties... omg, dat kan ik echt niet aan")
                return
            else:
                options = [i.strip()[:15] for i in d[1:]]
            query = d[0].strip()
            buttons = []
            for i,o in enumerate(options):
                buttons.append(InlineKeyboardButton(text=o,callback_data="poll%d:%d" % (len(self.polls),i)))
            keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
            sent = bot.sendMessage(chat_id, "Poll: %s" % query, reply_markup=keyboard)
            ident = telepot.message_identifier(sent)
            dataManager.add_poll(ident[0],ident[1],len(self.polls),query+"|"+"|".join(options),"{}")
            self.polls.append((ident, query, options))
            self.pollvotes.append({})
            
        #All the learning commands
        if rawcommand.startswith("/learn"):
            if rawcommand.find("->") == -1:
                bot.sendMessage(chat_id, "ik mis een '->' om aan te geven hoe de argumenten gescheiden zijn")
            call, response = rawcommand[7:].split("->",1)
            responses = [i.strip() for i in response.split("|") if i.strip()]
            if not responses:
                bot.sendMessage(chat_id, "geef geldige responses pl0x")
                return
            c = prepare_query(call)
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
                if c in self.aliasdict: self.userresponses[self.aliasdict[c]].extend(responses)
                else:
                    self.aliasdict[c] = len(self.userresponses)
                    self.userresponses[self.aliasdict[c]] = responses
            bot.sendMessage(chat_id, "ik denk dat ik het snap")
            return

        if rawcommand.startswith("/myresponses"):
            r = dataManager.get_user_responses(self.sender)
            s = "Lijst van je geleerde commando's:"
            for i, d in enumerate(r):
                s += "\n%d.: %s -> %s" % (i, d[0], d[1])
            lines = s.splitlines()
            for i in range(0, len(lines), 15):
                bot.sendMessage(chat_id, "\n".join(lines[i:i+15]))
            return

        if rawcommand.startswith("/deleteresponse"):
            n = rawcommand[16:].strip()
            if not n.isdigit():
                bot.sendMessage(chat_id, "dat is geen geldig getal")
                return
            if dataManager.delete_response(self.sender, int(n)):
                self.load_files()
                bot.sendMessage(chat_id, "Gelukt!")
            else:
                bot.sendMessage(chat_id, "hmm, iets ging mis. Check even of het getal daadwerkelijk klopt")
            return

        if rawcommand.startswith("/alias"):
            s = rawcommand[7:].strip()
            options = [prepare_query(i) for i in s.split("|")]
            if len(options) == 1:
                bot.sendMessage(chat_id, "geef wel synoniemen op door woorden te splitten met |")
                return
            if not all(options): #one of the options is empty
                bot.sendMessage(chat_id, "een van je gegeven opties is niet geldig (leeg)")
                return
            dataManager.add_alias(options, self.sender, msg['date'])
            for o in options:
                if o in self.aliasdict:
                    for oo in options:
                        self.aliasdict[oo] = self.aliasdict[o]
                    break #if they are not in the aliasdict then there are also no queries associated with it
            bot.sendMessage(chat_id, "deze dingen betekenen hetzelfde... got it!")
            return
                
        if rawcommand.startswith("/showalias"):
            s = prepare_query(rawcommand[11:])
            l = list(self.aliasdict.keys())
            if s in l: l.remove(s)
            if not s:
                bot.sendMessage(chat_id, "type een query na /showalias en ik laat zien welke synoniemen ik hier van ken")
                return
            if not s in self.aliasdict:
                options = difflib.get_close_matches(s,l)
                if not options:
                    bot.sendMessage(chat_id, "Deze query ken ik uberhaupt niet, misschien wil je me leren hoe ik er op moet reageren met /learn?")
                else:
                    bot.sendMessage(chat_id, "Ik ken deze niet, maar het lijkt wel op deze die ik wel ken: \n%s" % "\n".join(options))
                return
            i = self.aliasdict[s]
            aliases = [j[0] for j in filter(lambda x: x[1] == i, self.aliasdict.items())]
            count = len(self.userresponses[i])
            response = "Ik ken %d verschillende responses op deze query\n" % count
            if len(aliases) == 1:
                options = difflib.get_close_matches(s,l)
                if not options:
                    response += "Het lijkt er op dat ik geen synoniemen van deze term ken, misschien wil je me er een paar leren met /alias?"
                else:
                    response += "Ik ken geen synoniemen van deze term, maar hij lijkt wel veel op deze: \n%s\nIs ie gelijk aan een van deze?" % "\n".join(options)
            else:
                response += " | ".join(aliases)
            
            bot.sendMessage(chat_id, response)
            return

        if rawcommand.startswith("/myaliases"):
            r = dataManager.get_user_aliases(self.sender)
            s = "Lijst van je geleerde aliases:"
            for i, a in enumerate(r):
                s += "\n%d.: %s" % (i, a)
            lines = s.splitlines()
            for i in range(0, len(lines), 15):
                bot.sendMessage(chat_id, "\n".join(lines[i:i+15]))
            return

        if rawcommand.startswith("/deletealias"):
            n = rawcommand[13:].strip()
            if not n.isdigit():
                bot.sendMessage(chat_id, "dat is geen geldig getal")
                return
            if dataManager.delete_alias(self.sender, int(n)):
                self.load_files()
                bot.sendMessage(chat_id, "Gelukt!")
            else:
                bot.sendMessage(chat_id, "hmm, iets ging mis. Check even of het getal daadwerkelijk klopt")
            return
            
        t = msg['date']
        if t-self.morning_message_timer> 3600*16: #16 hours
            h = get_current_hour()
            if h>6 and h <12: #it is morning
                v = self.morning_message(PPA,command)
                if v:
                    self.morning_message_timer = t
                    self.sendMessage(PPA,v)
                    return

            
        if chat_id in self.silentchats:
            self.active = False
            return
        
        #now for the fun stuff :)

        #custom user commands
        c = prepare_query(rawcommand)
        if c in self.aliasdict:
            t = msg['date']
            if t-self.lastupdate > 1800: #every half hour update my willingness to say stuff
                self.update_querycounts(int((t-self.lastupdate)/1800))
                self.lastupdate = t
            if self.react_to_query(c):
                p = self.pick(self.userresponses[self.aliasdict[c]])
                p = p.replace("!name", self.sendername)
                if p: self.sendMessage(chat_id, p)
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
                if probaccept(0.07):
                    time.sleep(1.0)
                    self.sendMessage(chat_id, self.entertainment.get_joke())
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
            self.sendMessage(chat_id, self.entertainment.get_joke())
            return

        #weather
        val = startswith(command, self.commands["weather"])
        if val:
            self.sendMessage(chat_id, weather_report())
            return

        #refter menu
        if command.find("refter")!=-1:
            self.sendMessage(chat_id, reftermenu.get_todays_menu())
            return

        #facts
        val = startswith(command, self.commands["amuse"])
        if val:
            if probaccept(0.7):
                self.sendMessage(chat_id,self.entertainment.get_fact())
            elif probaccept(0.5):
                s = get_wikipedia.random_wiki_text()
                if s: self.sendMessage(chat_id,s)
            else: self.sendMessage(chat_id, self.entertainment.get_joke())
            return

        #spam check
        if startswith(command, self.commands["spam_ask"]):
            m = self.sendMessage(chat_id, "effe tellen")
            text = self.response_stats(chat_id)
            bot.editMessageText(telepot.message_identifier(m), text)
            #bot.sendMessage(chat_id, text)
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

        #try approximate custom matches
        options = difflib.get_close_matches(command,self.aliasdict.keys(),n=1,cutoff=0.9)
        if not options: options = difflib.get_close_matches(prepare_query(rawcommand),self.aliasdict.keys(),n=1,cutoff=0.9)
        if options:
            if self.react_to_query(options[0]):
                p = self.pick(self.userresponses[self.aliasdict[options[0]]])
                p = p.replace("!name", self.sendername)
                if p: bot.sendMessage(chat_id, p)
                return

        #haha... kont
        if command.find("kont")!=-1:
            self.sendMessage(chat_id, "Hahaha, je zei kont")
            return
        if command.find("cont")!=-1:
            self.sendMessage(chat_id, "Hahaha, je zei cont")
            return
        
        #questions and other random reactions
        if len(command)>6:
            if command[-5:].find("?")!=-1 or command[-5:].find("/")!=-1 or command[-5:].find(">")!=-1: #? and common misspellings
                if (command.find("wat vind")!=-1 or command.find("hoe denk")!=-1 or command.find("vind je")!=-1
                    or command.find("wat is je mening")!=-1 or command.find("wat denk")!=-1):
                    self.sendMessage(chat_id, self.pick(self.responses["question_opinion"]))
                elif startswith(command, ["heb","ben ","zijn ","was ","waren ","is ","ga","zal ","moet "]):
                    self.sendMessage(chat_id, self.pick(self.responses["question_degree"]))
                elif command.find("hoeveel")!=-1 or command.find("hoe veel")!=-1 or command.find("hoe vaak")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_amount"]))
                elif command.find("waarom")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_why"]))
                elif command.find("wat ")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_what"]))
                elif command.find("waarvoor ")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_waarvoor"]))
                elif command.find("waar ")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_where"]))
                elif command.find("wanneer")!=-1 or command.find("hoe laat")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_when"]))
                elif command.find("hoe ")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_how"]))
                elif command.find("welk")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_which"]))
                elif command.find("wie")!=-1:
                    self.sendMessage(chat_id, self.pick(self.responses["question_who"]))
                else: #yes/no question
                    self.sendMessage(chat_id, self.pick(self.responses["question_degree"]))
                return
            self.active = False
            if probaccept(0.05):
                bot.sendMessage(chat_id, self.entertainment.get_openingline())
                return
            elif probaccept(0.15):
                bot.sendMessage(chat_id,self.pick(self.responses["negative_response"]))
            elif probaccept(0.08):
                r = random.randint(0,len(self.userresponses)-1) # this works because the keys of userresponses are consecutive integers
                bot.sendMessage(chat_id, self.pick(self.userresponses[r]))
            return
        
        self.active = False


    def on_callback_query(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        print('Callback query:', query_id, from_id, data)
        if not data.startswith("poll"):
            return
        poll, option = data[4:].split(":")
        poll = int(poll)
        option = int(option)
        if str(from_id) in self.pollvotes[poll] and self.pollvotes[poll][str(from_id)] == option: return
        self.pollvotes[poll][str(from_id)] = option

        p = self.polls[poll]
        dataManager.add_poll(p[0][0],p[0][1], poll, p[1]+"|"+"|".join(p[2]), json.dumps(self.pollvotes[poll]))
        
        editor = telepot.helper.Editor(bot, self.polls[poll][0])
        buttons = []
        for i,o in enumerate(self.polls[poll][2]):
            c = sum(1 for k,v in self.pollvotes[poll].items() if v==i)
            if c == 0: s = o
            else: s = "%s %d" % (o, c)
            buttons.append(InlineKeyboardButton(text=s,callback_data="poll%d:%d" % (poll,i)))
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        editor.editMessageReplyMarkup(reply_markup=keyboard)
        bot.answerCallbackQuery(query_id, text="Je hebt gestemd op " + p[2][option])
        return

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
        total, topwords, p, char = dataManager.spam_stats(chat_id,hours=6)
        s = "Er zijn %d berichten verstuurd in de afgelopen 6 uur" % total
        s += "\nHardste spammers: "
        for i in range(min([len(p),3])):
            n, c = p[i][0], p[i][1]
            name = bot.getChatMember(chat_id, n)['user']['first_name']
            s += name + " (%d) " % c
        s += "\nMeest voorkomende woorden: %s" % ", ".join(topwords)
        s += "\nKarakteristieke woorden: %s" % ", ".join(char)
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
