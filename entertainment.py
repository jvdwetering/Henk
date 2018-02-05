import os
import json

datadir = "datafiles"

class Entertainment(object):
    def __init__(self):
        self.load()

    def load(self):
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

    def update_counters(self, v):
        self.counters[v] += 1
        f = open(os.path.join(datadir,"counters.json"),"w")
        json.dump(self.counters,f)
        return self.counters[v]-1

    def get_joke(self):
        return self.jokes[self.update_counters("jokes")]

    def get_openingline(self):
        return self.openinglines[self.update_counters("lines")]

    def get_fact(self):
        return self.facts[self.update_counters("facts")]

    def get_sonnet(self):
        return self.sonnets[self.update_counters("sonnets")]
