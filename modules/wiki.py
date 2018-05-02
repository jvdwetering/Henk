import requests
import urllib

from .base import Module
from util import startswith, probaccept

s = "http://nl.wikipedia.org/wiki/Speciaal:Willekeurig"

def random_wiki_text():
    try:
        url = urllib.request.urlopen(s,timeout=1.5).geturl()
    
        name = url.rsplit("/",1)[1]
        return wiki_text(name)
    
    except:
        return ""

def wiki_text_exact(name):
    try:
        response = requests.get(
            'https://nl.wikipedia.org/w/api.php',
            params={
                'action': 'query',
                'format': 'json',
                'titles': name,
                'prop': 'extracts',
                'exintro': True,
                'explaintext': True,
            },
            timeout=1.5).json()

        text = next(iter(response['query']['pages'].values()))['extract']
        return text
    
    except:
        return ""

def wiki_text(name):
    try:
        response = requests.get(
            'https://nl.wikipedia.org/w/api.php',
            params={
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': name,
                'srlimit': 3
            },
            timeout=1.5).json()
    except:
        return ""
    try:
        s = response['query']['search'][0]['title']
    except:
        return ""
    s = wiki_text_exact(s)
    return s


class Wiki(Module):
    def register_commands(self, bot):
        bot.add_slash_command("wiki", self.wiki)
        bot.add_command_category("question", self.wiki)

    def wiki(self, bot, msg):
        if msg.normalised.find("moeder")!=-1:
                return bot.pick(bot.responses["je_moeder"])
        t = msg.raw[-len(msg.command):] # we need the original because capitalization is important
        t = t.replace("?","").replace("!","").replace(".","").replace('"',"").strip()
        res = wiki_text(t)
        if res: return res
        else:
            if probaccept(0.5):
                return bot.pick(bot.responses["wiki_failure"])
            else: return bot.pick(bot.responses["negative_response"])

wiki = Wiki()