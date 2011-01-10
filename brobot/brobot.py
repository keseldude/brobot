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
import sys

def main():
    brobot_path = os.path.abspath(__file__)
    brobot_dir = os.path.dirname(brobot_path)
    settings_path = os.path.join(brobot_dir, 'settings.yml')
    f = open(settings_path)
    settings = yaml.load(f)
    
    settings['brobot_path'] = brobot_path
    settings['base_path'] = brobot_dir
    settings['python_binary'] = sys.executable
    
    from core import bot
    
    brobot = bot.IRCBot(settings)
    brobot.start()

if __name__ == '__main__':
    main()
