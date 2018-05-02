import os
import json
import random

from .base import Module
from .wiki import random_wiki_text
from util import datadir, probaccept

class Entertainment(Module):
    def initialise(self, bot):
        f = open(os.path.join(datadir,"grappen.txt"),"r",encoding='latin-1')
        self.jokes = f.read().splitlines()
        f.close()
        f = open(os.path.join(datadir,"weetjes.txt"),"r",encoding='latin-1')
        self.facts = f.read().splitlines()
        f.close()
        f = open(os.path.join(datadir,"zinnen.txt"),"r",encoding='latin-1')
        self.openinglines = f.read().splitlines()
        f.close()

        f = open(os.path.join(datadir,"sonnets.txt"),"r",encoding='latin-1')
        self.sonnets = [s.strip("\n") for s in f.read().split("\n\n")]
        f.close()
        
        f = open(os.path.join(datadir,"counters.json"),"r")
        self.counters = json.load(f)
        f.close()

    def register_commands(self,bot):
        bot.add_command_category("funny", self.get_joke)
        bot.add_command_category("amuse", self.amuse)
        bot.add_command_category("spam_react", self.spam)

    def update_counters(self, v):
        self.counters[v] += 1
        f = open(os.path.join(datadir,"counters.json"),"w")
        json.dump(self.counters,f)
        return self.counters[v]-1

    def amuse(self, bot, msg):
        if probaccept(0.6):
            return self.get_fact()
        if probaccept(0.5):
            return self.get_sonnet()
        if probaccept(0.5):
            s = random_wiki_text()
            if s: return s
        return self.get_joke()

    def spam(self, bot, msg):
        if probaccept(0.4):
            return "spam"*random.randint(3,15)
        if probaccept(0.3):
            return self.get_openingline()
        s = random_wiki_text()
        if s: return s
        return self.get_fact()

    def get_joke(self, *args):
        return self.jokes[self.update_counters("jokes")]

    def get_openingline(self, *args):
        return self.openinglines[self.update_counters("lines")]

    def get_fact(self, *args):
        return self.facts[self.update_counters("facts")]

    def get_sonnet(self, *args):
        return self.sonnets[self.update_counters("sonnets")]

entertainment = Entertainment()