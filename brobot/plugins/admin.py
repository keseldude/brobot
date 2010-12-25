#===============================================================================
# brobot
# Copyright (C) 2010  Michael Keselman
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#===============================================================================

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
        
    
