from core import bot

class JoinPlugin(bot.CommandPlugin):
    name = 'join'
    admin = True
    def process(self, connection, source, target, args):
        if self.ircbot.is_admin(connection.server, source.nick) and \
            1 <= len(args) <= 2:
            self.ircbot.join(connection, u' '.join(args))
    

class PartPlugin(bot.CommandPlugin):
    name = 'part'
    admin = True
    def process(self, connection, source, target, args):
        if self.ircbot.is_admin(connection.server, source.nick):
            args_len = len(args)
            if args_len == 0:
                self.ircbot.part(connection, target)
            elif args_len == 1:
                self.ircbot.part(connection, args[0])
    

class QuitPlugin(bot.CommandPlugin):
    name = 'quit'
    admin = True
    def process(self, connection, source, target, args):
        if self.ircbot.is_admin(connection.server, source.nick):
            self.ircbot.quit(connection, message=u' '.join(args))
    

class ExitPlugin(bot.CommandPlugin):
    name = 'exit'
    admin = True
    def process(self, connection, source, target, args):
        if self.ircbot.is_admin(connection.server, source.nick):
            self.ircbot.exit()
        
    
