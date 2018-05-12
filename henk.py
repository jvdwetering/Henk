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
import math
import json
import urllib3
from collections import OrderedDict

import difflib

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InlineQueryResultArticle, InlineQueryResultPhoto, InputTextMessageContent


from managedata import ManageData
import longstrings
from util import get_current_hour, normalise, prepare_query, startswith, probaccept, Message
import modules



class Henk(object):
    def __init__(self, telebot, isdummy=False):
        self.telebot = telebot # the bot interface for Telegram
        self.dataManager = ManageData() #interface to the database
        if isdummy: self.dataManager.dummy = True
        self.should_exit = False

        self.querycounts = {} #counts how many times I've said a thing lately
        self.lastupdate = 0 #how long it has been since I've updated querycounts
        self.active = False #whether someone has just talked to me
        
        self.morning_message_timer = 0 #how long ago we have said a morning message

        self.slashcommands = OrderedDict() # command:callback where the callback takes two arguments, (self,msg)
        self.commandcategories = OrderedDict() #commandtype:callback where commandtype is a key in self.commands
        self.callback_query_types = OrderedDict() #ident:callback for special reply actions from Telegram

        self.load_files() #must be called before module.register_commands

        for module in modules.modules:
            module.register_commands(self)

        #PPA = -6722364 #hardcoded label for party pownies
        self.homegroup = -218118195 #Henk's fun palace

        self.admin_ids = [19620232] #John

    def add_slash_command(self,command, callback):
        if command in self.slashcommands:
            raise Exception("Slashcommand %s is already implemented" % command)
        self.slashcommands[command] = callback
        return

    def add_command_category(self, command, callback):
        if command in self.commandcategories:
            raise Exception("Command Category %s is already implemented" % command)
        if command not in self.commands:
            raise Exception("Unknown command category %s" % command)
        self.commandcategories[command] = callback

    def add_callback_query(self, ident, callback):
        if ident in self.callback_query_types:
            raise Exception("Callback ident %s already used" % ident)
        self.callback_query_types[ident] = callback

    def build_response_dict(self):
        aliases = self.dataManager.get_all_aliases()
        self.aliasdict = {} #mapping a query to an int
        #usually we will call pick(self.userresponses[self.aliasdict[query]])
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

        d = self.dataManager.get_all_responses()
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

    def load_files(self):
        f = open("commands.json","r")
        d = json.load(f) #dictionary of lists of variations of commands and responses
        f.close()
        self.commands = d["commands"]
        self.responses = d["responses"]

        self.build_response_dict()
        
        self.silentchats = self.dataManager.get_silent_chats()
        for module in modules.modules:
            module.initialise(self)

    def sendMessage(self, chat_id, s):
        m = self.telebot.sendMessage(chat_id, s)
        if probaccept(0.7): self.active = True
        else: self.active = False
        return m

    def pick(self, options):
        return random.sample(options,1)[0].replace("!name", self.sendername)

    def update_querycounts(self, amount):
        for q in self.querycounts:
            self.querycounts[q] = max([0,self.querycounts[q]-amount])

    def react_to_query(self, q):
        '''Determine whether we will react to this specific query based on if we did so previously, to prevent spam'''
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
            elif msg.find('morgen')!=-1: self.sendMessage(chat_id, msg)
            else: self.sendMessage(chat_id,"Goedemorgen")
            time.sleep(1.0)
            if probaccept(0.5):
                return modules.weather.weather_report()
            elif probaccept(0.5):
                return modules.entertainment.get_sonnet()
            elif probaccept(0.5):
                return modules.entertainment.get_joke()
            else:
                return modules.entertainment.get_openingline()
        else:
            return None

    def on_chat_message(self, message):
        msg = Message(message)
        if not msg.istext:
            print('Chat:', msg.content_type, msg.chat_type, msg.chat_id)
            self.active = False
            return

        self.dataManager.write_message(msg.object)
        rawcommand = msg.raw
        command = msg.normalised
        self.sendername = msg.sendername
        try:
            print('Chat:', msg.chat_type, msg.chat_id, msg.normalised)
        except UnicodeDecodeError:
            print('Chat:', msg.chat_type, msg.chat_id, msg.normalised.encode('utf-8'))

        #slash commands first
        if msg.raw.startswith("/"):
            for k in self.slashcommands.keys():
                if msg.raw[1:].startswith(k):
                    msg.command = msg.raw[len(k)+2:].strip()
                    v = self.slashcommands[k](self, msg)
                    if v: self.sendMessage(msg.chat_id, v)
                    return
        
        #Morning message
        if msg.date-self.morning_message_timer> 3600*16: #16 hours since last message
            h = get_current_hour()
            if h>6 and h <12: #it is morning
                v = self.morning_message(self.homegroup,command)
                if v:
                    self.morning_message_timer = msg.date
                    self.sendMessage(self.homegroup,v)
                    return

        if msg.chat_id in self.silentchats:
            self.active = False
            return
        
        #now for the fun stuff :)

        #custom user responses
        c = prepare_query(msg.raw)
        if c in self.aliasdict:
            t = msg.date
            if t-self.lastupdate > 1800: #every half hour update my willingness to say stuff
                self.update_querycounts(int((t-self.lastupdate)/1800))
                self.lastupdate = t
            if self.react_to_query(c):
                p = self.pick(self.userresponses[self.aliasdict[c]])
                p = p.replace("!name", msg.sendername)
                if p: self.sendMessage(msg.chat_id, p)
                return
            
        #respond to cussing
        if startswith(msg.normalised.replace(", "," "), self.commands['cuss_out']):
            self.sendMessage(msg.chat_id, self.pick(self.responses['cuss_out']))
            return
        command = msg.normalised
        for i in self.commands['introductions']:
            if command.startswith(i):
                command = command[len(i)+1:].strip()
                break
        else:
            if not self.active: return #no introduction given and not active
        if command.startswith(","): command = command[1:].strip()
        if command.startswith("."): command = command[1:].strip()

        #No further command is given so we just say hi
        if not command:
            try:
                name = msg.sendername
                if name == "Olaf": name = "Slomp"
                val = self.pick(self.responses["hi"]).replace("!name",name)
                self.sendMessage(msg.chat_id, val)
                if probaccept(0.07):
                    time.sleep(1.0)
                    self.sendMessage(msg.chat_id, modules.entertainment.get_joke())
                return
            except KeyError:
                self.active = False
                return

        #check if the command corresponds to a module
        for cmd in self.commandcategories.keys():
            s = startswith(command, self.commands[cmd])
            if s:
                msg.command = command[len(s)+1:].strip()
                r = self.commandcategories[cmd](self, msg)
                if r and type(r)==str: self.sendMessage(msg.chat_id, r)
                return
        
        #try approximate custom matches
        options = difflib.get_close_matches(command,self.aliasdict.keys(),n=1,cutoff=0.9)
        if not options: options = difflib.get_close_matches(prepare_query(msg.raw),self.aliasdict.keys(),n=1,cutoff=0.9)
        if options:
            if self.react_to_query(options[0]):
                p = self.pick(self.userresponses[self.aliasdict[options[0]]])
                p = p.replace("!name", msg.sendername)
                if p: self.sendMessage(msg.chat_id, p)
                return

        #haha... kont
        if command.find("kont")!=-1:
            self.sendMessage(msg.chat_id, "Hahaha, je zei kont")
            return
        if command.find("cont")!=-1:
            self.sendMessage(msg.chat_id, "Hahaha, je zei cont")
            return
        
        #questions and other random reactions
        if len(command)>6:
            chat_id = msg.chat_id
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
                self.sendMessage(chat_id, modules.entertainment.get_openingline())
            elif probaccept(0.15):
                self.sendMessage(chat_id,self.pick(self.responses["negative_response"]))
            elif probaccept(0.08):
                r = random.randint(0,len(self.userresponses)-1) # this works because the keys of userresponses are consecutive integers
                self.sendMessage(chat_id, self.pick(self.userresponses[r]))
            return
        
        self.active = False
        return


    def on_callback_query(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        print('Callback query:', query_id, from_id, data)
        for ident,callback in self.callback_query_types.items():
            if data.startswith(ident):
                callback(self,msg)
                return
        print("Unkown callback query: %s" % data)

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


if __name__ == '__main__':

    f = open("apikey.txt", "r")
    TOKEN = f.read() #token for Henk
    f.close()

    #PPA = -6722364 #hardcoded label for party pownies
    PPA = -218118195 #Henk's fun palace

    ADMIN = 19620232 #John

    telebot = telepot.Bot(TOKEN)
    answerer = telepot.helper.Answerer(telebot)
    
    try: 
        henk = Henk(telebot)
        MessageLoop(telebot, {'chat': henk.on_chat_message,
                          'callback_query': henk.on_callback_query,
                          'inline_query': henk.on_inline_query,
                          'chosen_inline_result': henk.on_chosen_inline_result}).run_as_thread()
        print('Listening ...')

        silent=False

        h = get_current_hour()
        #if not silent:
        #    if h>6 and h<13:
        #        telebot.sendMessage(PPA,"Goedemorgen")
        #    elif h>12 and h<19:
        #        telebot.sendMessage(PPA,"Goedemiddag")
        #    else:
        #       telebot.sendMessage(PPA,"Goedeavond")

        # Keep the program running.
        while True:
            try:
                if henk.should_exit:
                    break
                time.sleep(1)
            except ConnectionResetError:
                print("ConnectionResetError")
            except urllib3.exceptions.ProtocolError:
                print("ProtocolError")
    except KeyboardInterrupt:
        pass
    finally:
        henk.dataManager.close()
        if not henk.should_exit:
            telebot.sendMessage(PPA,"Ik ga even slapen nu. doei doei")
