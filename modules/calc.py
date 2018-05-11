import math

import telepot
import simpleeval #for evaluating math expressions
simpleeval.MAX_POWER=1000

math_constants = {"pi": math.pi, "e": math.e, "true": True, "false": False, "True": True, "False": False}
math_functions = {"sin": math.sin, "cos": math.cos, "sqrt": math.sqrt, "ln": math.log, "log": math.log10}

from .base import Module


class Calc(Module):
    def register_commands(self, bot):
        bot.add_slash_command("calc", self.calc)
        bot.add_slash_command("stats", self.stats)
        bot.add_slash_command("learnstats", self.learnstats)

        bot.add_command_category("math", self.calc)
        bot.add_command_category("spam_ask", self.stats)

    def calc(self, bot, msg):
        text = msg.command
        if text.endswith("?"): text = text[:-1]
        return self.response_math(text,bot,clean=True)

    def stats(self, bot, msg):
        m = bot.sendMessage(msg.chat_id, "effe tellen")
        text = self.response_stats(bot, msg.chat_id)
        bot.editMessageText(telepot.message_identifier(m), text)
        return

    def learnstats(self, bot, msg):
        r = bot.dataManager.get_all_responses()
        c = len(r)
        d = sum([len(i) for i in r.values()])
        a = bot.dataManager.get_all_aliases()
        aa = sum([len(i) for i in a])
        return "Ik ken %d custom queries, en heb daar in totaal %d responses op. Verder ken ik %d aliases" % (c,d, aa)


    def response_math(self, t ,bot, clean=False): #if not clean it outputs random error messages
        try:
            result = simpleeval.simple_eval(t.replace("^","**"),functions=math_functions, names=math_constants)
            if type(result) == bool:
                if result: result = "waar"
                else: result = "niet waar"
            return "Dat is " + str(result)
        except (simpleeval.InvalidExpression, simpleeval.FunctionNotDefined,
                simpleeval.AttributeDoesNotExist,KeyError):
            if not clean: return bot.pick(bot.commands["math_error"])
            else: return "Sorry, dat snap ik niet :("
        except simpleeval.NumberTooHigh:
            return "Sorry, dat is te moeilijk voor me"
        except Exception:
            return "computer says no"

    def response_stats(self, bot, chat_id):
        total, topwords, p, char = bot.dataManager.spam_stats(chat_id,hours=6)
        s = "Er zijn %d berichten verstuurd in de afgelopen 6 uur" % total
        s += "\nHardste spammers: "
        for i in range(min([len(p),3])):
            n, c = p[i][0], p[i][1]
            name = bot.telebot.getChatMember(chat_id, n)['user']['first_name']
            s += name + " (%d) " % c
        s += "\nMeest voorkomende woorden: %s" % ", ".join(topwords)
        s += "\nKarakteristieke woorden: %s" % ", ".join(char)
        return s

calc = Calc()
