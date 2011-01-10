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
from core.irc.structures import User
from datetime import datetime

class UptimePlugin(bot.CommandPlugin):
    name = 'uptime'
    def load(self):
        self.start_time = datetime.utcnow()
    
    def format_timedelta(self, delta):
        message = ''
        if delta.days > 0:
            message += '%s days ' % delta.days
        
        hours = delta.seconds // 3600
        seconds = delta.seconds - (hours * 3600)
        minutes = seconds // 60
        seconds = seconds - (minutes * 60)
        
        if hours > 0:
            message += '%s hours ' % hours
        if minutes > 0:
            message += '%s min ' % minutes
        if seconds > 0:
            message += '%s sec ' % seconds
        
        return message.strip()
    
    def process(self, connection, source, target, args):
        delta = datetime.utcnow() - self.start_time
        return {'action': self.Action.PRIVMSG,
                'target': target,
                'message': (self.format_timedelta(delta),)
                }
    
