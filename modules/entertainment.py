import os
import json
import random
import time

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

        f = open(os.path.join(datadir,"silmarillion.txt"),"r",encoding='utf-8')
        self.silmaril = [s.strip("\n") for s in f.read().split("\n\n")]
        f.close()
        
        f = open(os.path.join(datadir,"counters.json"),"r")
        self.counters = json.load(f)
        f.close()

        self.tolkien_calls = []

    def register_commands(self,bot):
        bot.add_command_category("funny", self.get_joke)
        bot.add_command_category("amuse", self.amuse)
        bot.add_command_category("spam_react", self.spam)

        bot.add_slash_command("tolkien", self.tolkien)

    def get_item(self, l, v):
        try:
            result = l[self.counters[v]]
            self.counters[v] += 1
        except KeyError:  # Time to reset the counter
            self.counters[v] = 0
            result = l[self.counters[v]]
        f = open(os.path.join(datadir,"counters.json"),"w")
        json.dump(self.counters,f)
        return result

    def amuse(self, bot, msg):
        if probaccept(0.6):
            return self.get_fact()
        if probaccept(0.5):
            return self.get_silmaril()
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
        return self.get_item(self.jokes, "jokes")

    def get_openingline(self, *args):
        return self.get_item(self.openinglines, "lines")

    def get_fact(self, *args):
        return self.get_item(self.facts, "facts")

    def get_sonnet(self, *args):
        return self.get_item(self.sonnets, "sonnets")

    def get_silmaril(self, *args):
        s = self.get_item(self.silmaril, "silmaril")
        self.tolkien_calls.append((time.time(),len(s)))
        return f"{self.counters['silmaril']}. {s}"

    def tolkien(self, bot, msg):
        s = msg.command.strip()
        ct = time.time()
        total_tolkien = 0
        for t, v in self.tolkien_calls:
            if ct-t < 2600*18: total_tolkien += v
        if total_tolkien > 3000:
            return "Dat is wel genoeg Tolkien voor vandaag"

        if not s:
            return self.get_silmaril()

        try:
            i = int(s)
            s = self.silmaril[i]
            return s
        except (ValueError, KeyError, IndexError):
            return "Of type /tolkien, of type /tolkien n, waar n een getal is die de paragraaf aangeeft."


entertainment = Entertainment()