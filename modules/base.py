class Module(object):
    def initialise(self, bot):
        pass

    def register_commands(self, bot):
        '''
        should call 
        bot.add_slash_command("slashcommand", self.callback)
        bot.add_command_category("commandtype", self.callback)
        bot.add_callback_query("ident", self.callback)
        '''
        pass

    def callback(self,bot,msg):
        '''
        Callback for when the slash command is given.
        If it returns a string, this string is sent back to the sender
        msg is a util.Message object
        '''
        pass