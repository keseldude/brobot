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

import yaml
import os
import os.path
import sys
import logging

class Brobot(object):
    def __init__(self, brobot_path):
        self.brobot_path = brobot_path
        self.brobot_dir = os.path.dirname(self.brobot_path)
        self.settings_path = os.path.join(self.brobot_dir, 'settings.yml')
        
        self.ircbot = None
        self.load_ircbot()
    
    def load_ircbot(self):
        from core import bot
        settings = self.load_settings()
        self.ircbot = bot.IRCBot(settings)
    
    def start(self):
        restart = self.ircbot.start()
        if restart:
            sys.exit(3)
    
    def exit(self):
        self.ircbot.exit()
    
    def load_settings(self):
        f = open(self.settings_path)
        settings = yaml.load(f)
        
        settings['brobot_path'] = self.brobot_path
        settings['base_path'] = self.brobot_dir
        settings['python_binary'] = sys.executable
        
        return settings
    

def main():
    brobot_path = os.path.abspath(__file__)
    brobot = Brobot(brobot_path)
    try:
        brobot.start()
    except KeyboardInterrupt:
        brobot.exit()
    sys.exit(0)

def restart_with_reboot():
    while True:
        args = [sys.executable] + sys.argv
        if sys.platform == 'win32':
            args = ['"%s"' % arg for arg in args]
        new_env = os.environ.copy()
        new_env['RUN_MAIN'] = 'TRUE'
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_env)
        if exit_code != 3:
            return exit_code

if __name__ == '__main__':
    if os.environ.get('RUN_MAIN') == 'TRUE':
        main()
    else:
        try:
            exit_code = restart_with_reboot()
            if exit_code < 0:
                os.kill(os.getpid(), -exit_code)
            else:
                sys.exit(exit_code)
        except KeyboardInterrupt:
            pass
