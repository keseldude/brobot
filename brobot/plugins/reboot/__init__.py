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
from subprocess import Popen
from threading import Thread
import os.path

class RebootPlugin(bot.CommandPlugin):
    name = 'reboot'
    admin = True
    reboot_script_path = \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '_reboot.py')
    def load(self):
        self.python_binary = self.ircbot.settings['python_binary']
        self.brobot_path = \
                        os.path.expanduser(self.ircbot.settings['brobot_path'])
    
    def reboot(self):
        self.ircbot.exit()
        Popen([self.python_binary, self.reboot_script_path,
                   self.ircbot.pid_path, self.python_binary, self.brobot_path])
    
    def process(self, connection, source, target, args):
        if self.ircbot.is_admin(connection.server, source.nick):
            t = Thread(target=self.reboot)
            t.daemon = False
            t.start()
    
