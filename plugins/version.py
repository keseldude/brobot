from core import bot

class VersionPlugin(bot.Plugin):
    def __init__(self, ircbot):
        super(VersionPlugin, self).__init__(ircbot, 'version')
    
    def process(self, connection, source, target, args):
        self.ircbot.privmsg(connection, target, self.ircbot.get_version())
    
