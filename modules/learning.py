from collections import defaultdict

from .base import Module
from util import prepare_query
import difflib

class Learning(Module):
    def register_commands(self,bot):
        bot.add_slash_command("learn", self.learn)
        bot.add_slash_command("myresponses", self.myresponses)
        bot.add_slash_command("deleteresponse", self.deleteresponse)
        bot.add_slash_command("alias", self.alias)
        bot.add_slash_command("showalias", self.showalias)
        bot.add_slash_command("myaliases", self.myaliases)
        bot.add_slash_command("deletealias", self.deletealias)


    def learn(self, bot, msg):
        if msg.raw.find("->") == -1:
            return "ik mis een '->' om aan te geven hoe de argumenten gescheiden zijn"
        call, response = msg.raw[7:].split("->",1)
        responses = [i.strip() for i in response.split("|") if i.strip()]
        if not responses:
            return "Geef geldige responses pl0x"
        c = prepare_query(call)
        if c in (bot.commands["introductions"] + bot.commands["funny"]
                 + bot.commands["amuse"] + bot.commands["spam_ask"]):
            return "Deze query mag niet (beschermd)"
        if c.startswith("/"):
            return "queries mogen niet beginnen met /"
        if c.startswith("$"): #special command
            if c[1:] not in bot.responses.keys():
                return "geen geldig label"
            else: bot.responses[c[1:]].extend(responses)
        bot.dataManager.add_response(c, responses, msg.sender, msg.date)
        if not c.startswith("$"):
            if c in bot.aliasdict: bot.userresponses[bot.aliasdict[c]].extend(responses)
            else:
                bot.aliasdict[c] = len(bot.userresponses)+1 #add new to list of aliases
                bot.userresponses[bot.aliasdict[c]] = responses
        return "Ik denk dat ik het snap"

    def myresponses(self, bot, msg):
        responses = bot.dataManager.get_user_responses(msg.sender)

        msg.command.split()
        s = "Lijst van je geleerde commando's:"

        if "grouped" in msg.command.split():
            responses_per_call = defaultdict(list)
            for d in responses:
                responses_per_call[d[0]].append(d[1])

            for command, responses in responses_per_call.items():
                s += "\n%s -> %s" % (command, " | ".join(responses))
        else:
            for i, d in enumerate(responses):
                s += "\n%d.: %s -> %s" % (i, d[0], d[1])

        lines = s.splitlines()
        for i in range(0, len(lines), 15):
            bot.sendMessage(msg.chat_id, "\n".join(lines[i:i+15]))
        return

    def deleteresponse(self, bot, msg):
        n = msg.command
        if not n.isdigit():
            return "Dat is geen geldig getal"
        if bot.dataManager.delete_response(msg.sender, int(n)):
            bot.build_response_dict()
            return "Gelukt!"
        else:
            return "hmm, iets ging mis. Check even of het getal daadwerkelijk klopt"

    def alias(self, bot, msg):
        s = msg.command
        options = [prepare_query(i) for i in s.split("|")]
        if len(options) == 1:
            return "geef wel synoniemen op door woorden te splitten met |"
        if not all(options): #one of the options is empty
            return "een van je gegeven opties is niet geldig (leeg)"
        matches = [o for o in options if o in bot.aliasdict]
        if not matches:
            return "ik ken nog geen responses voor deze queries, voeg die eerst toe alsjeblieft"
        bot.dataManager.add_alias(options, msg.sender, msg.date)
        if len(matches) == 1:
            for o in options: #match all the new aliases to the known one
                bot.aliasdict[o] = bot.aliasdict[matches[0]]
        else: #two sets of queries now point to the same thing, we need to reload the entire structure
            bot.build_response_dict()
        return "deze dingen betekenen hetzelfde... got it!"

    def showalias(self, bot, msg):
        s = prepare_query(msg.raw[11:])
        if not s:
            return "type een query na /showalias en ik laat zien welke synoniemen ik hier van ken"
        l = bot.aliasdict.keys()
        if not s in l:
            options = difflib.get_close_matches(s,l)
            if not options:
                return "Deze query ken ik uberhaupt niet, misschien wil je me leren hoe ik er op moet reageren met /learn?"
            else:
                return "Ik ken deze niet, maar het lijkt wel op deze die ik wel ken: \n%s" % "\n".join(options)
        i = bot.aliasdict[s]
        aliases = [k for k,v in bot.aliasdict.items() if v==i]
        count = len(bot.userresponses[i])
        response = "Ik ken %d verschillende responses op deze query\n" % count
        if len(aliases) == 1:
            options = difflib.get_close_matches(s,l)
            if s in options: options.remove(s)
            if not options:
                response += "Het lijkt er op dat ik geen synoniemen van deze term ken, misschien wil je me er een paar leren met /alias?"
            else:
                response += "Ik ken geen synoniemen van deze term, maar hij lijkt wel veel op deze: \n%s\nIs ie gelijk aan een van deze?" % "\n".join(options)
        else:
            response += " | ".join(aliases)
        
        return response

    def myaliases(self, bot, msg):
        r = bot.dataManager.get_user_aliases(msg.sender)
        s = "Lijst van je geleerde aliases:"
        for i, a in enumerate(r):
            s += "\n%d.: %s" % (i, a)
        lines = s.splitlines()
        for i in range(0, len(lines), 15):
            bot.sendMessage(msg.chat_id, "\n".join(lines[i:i+15]))
        return


    def deletealias(self, bot, msg):
        n = msg.command
        if not n.isdigit():
            return "dat is geen geldig getal"
        if bot.dataManager.delete_alias(msg.sender, int(n)):
            bot.build_response_dict()
            return "Gelukt!"
        else:
            return "hmm, iets ging mis. Check even of het getal daadwerkelijk klopt"


learning = Learning()