from core import bot
from core.irc.structures import Channel
import itertools

class UsersPlugin(bot.CommandPlugin):
    name = 'users'
    def process(self, connection, source, target, args):
        channel = self.ircbot.find_channel(connection.server, target)
        if channel is not None:
            generator = itertools.imap(repr, channel.users)
            self.ircbot.privmsg(connection, target,
                '%d Users in the channel.' % len(channel.users))

    
