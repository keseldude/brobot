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

class ComposePlugin(bot.CommandPlugin):
    name = 'compose'
    def find_plugin(self, name, plugins):
        for commands, plugin in plugins:
            if name in commands:
                return plugin
        return None
    
    def process(self, connection, source, target, args):
        args_len = len(args)
        if args_len < 2:
            return None
        
        try:
            num_args = int(args[0])
        except ValueError:
            num_args = 2
        else:
            args = args[1:]
            args_len -= 1
        
        if args_len < num_args:
            return None
        
        plugins = self.ircbot.command_plugins['BOTH'].items()
        funcs, func_args = args[:num_args], args[num_args:]
        
        plugin_stack = []
        
        for func in funcs:
            plugin = self.find_plugin(func, plugins)
            if plugin is None:
                return None
            plugin_stack.insert(0, plugin)
        
        first, rest = plugin_stack[0], plugin_stack[1:]
        result = first.process(connection, source, target, func_args)
        try:
            message = u'\n'.join(result['message'])
        except KeyError:
            return None
        
        for plugin in rest:
            result = plugin.process(connection, source, target, (message,))
            try:
                message = u'\n'.join(result['message'])
            except KeyError:
                return None
        return self.privmsg(target, message.split(u'\n'))
    
