from ..base import Module

class Games(Module):
    def initialise(self, bot):
        pass

    def register_commands(self, bot):
        '''
        should call 
        bot.add_slash_command("slashcommand", self.callback)
        bot.add_command_category("commandtype", self.callback)
        bot.add_callback_query("ident", self.callback)
        '''
        bot.add_slash_command("klaverjassen", self.klaverjassen)

    def klaverjassen(self,bot,msg):
        return "We gaan klaverjassen!"

games = Games()
