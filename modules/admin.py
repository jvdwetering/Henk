from .base import Module
import longstrings

class Admin(Module):
    def register_commands(self,bot):
        bot.add_slash_command("help", self.help)
        bot.add_slash_command("learnhelp", self.learnhelp)
        bot.add_slash_command("say ", self.say)
        bot.add_slash_command("reload", self.reload)
        bot.add_slash_command("setsilent", self.setsilent)
        bot.add_slash_command("quit", self.quit)

        bot.add_command_category("whatcanyoudo", self.help)
        bot.add_command_category("howdoyoulearn", self.learnhelp)


    def help(self, bot, msg):
        if msg.chat_id in bot.silentchats:
            return longstrings.helpsilent
        else: return  longstrings.helptext
    
    def learnhelp(self, bot, msg):
        return longstrings.learnhelp
    
    def say(self, bot, msg):
        if msg.sender in bot.admin_ids:
            bot.sendMessage(bot.homegroup, msg.raw[4:])
        return

    def quit(self, bot, msg):
        if msg.sender in bot.admin_ids:
            bot.should_exit = True
            return "Quitting"

    def reload(self, bot, msg):
        if msg.sender in bot.admin_ids:
            bot.load_files()
            return "reloading files"
        else:
            return "I'm afraid I can't let you do that"

    def setsilent(self, bot, msg):
        t = msg.command
        if not t.isdigit():
            return "1 of 0 aub"
        else:
            v = int(bool(int(t)))
            bot.dataManager.set_silent_mode(chat_id, v)
            if v == 1 and not chat_id in bot.silentchats:
                bot.silentchats.append(chat_id)
            if v == 0 and chat_id in self.silentchats:
                bot.silentchats.remove(chat_id)
            return "done"

admin = Admin()