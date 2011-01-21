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
    
    def reload_modules(self):
        root_logger = logging.getLogger('')
        root_logger.handlers = []
        
        for module in sys.modules.values():
            mod_path = getattr(module, '__file__', None)
            if mod_path is not None and mod_path != __file__ and \
                mod_path.startswith(self.brobot_dir):
                reload(module)
    
    def start(self):
        restart = self.ircbot.start()
        while restart:
            self.reload_modules()
            self.load_ircbot()
            restart = self.ircbot.start()
    
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
    brobot.start()

if __name__ == '__main__':
    main()
