from core import bot

class VersionPlugin(bot.CommandPlugin):
    name = 'version'
    def process(self, connection, source, target, args):
        self.ircbot.privmsg(connection, target, self.ircbot.get_version())
    
