"""
brobot
Copyright (C) 2010  Michael Keselman

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

import irc
import itertools
from multiprocessing import Process

class Plugin(object):
    def __init__(self, ircbot, name):
        self.ircbot = ircbot
        self.name = name
    
    def process(self, connection, source, target, args):
        raise NotImplementedError
    

class EventPlugin(Plugin):
    def process(self, connection, source='', target='', args=[], message=''):
        raise NotImplementedError
    

class IRCBot(irc.Client):
    def __init__(self, settings):
        self.settings = settings
        
        self.admins = {}
        self.initial_channels = {}
        
        servers = []
        for server in settings['servers']:
            irc_server = irc.Server(server['host'], server['port'], server['nick'])
            servers.append(irc_server)
            self.admins[irc_server] = server['admins']
            self.initial_channels[irc_server] = server['channels']
        
        plugin_path = settings['plugin_path']
        
        self.command_plugins = {}
        for msg_type, command_plugins in settings['command_plugins'].iteritems():
            self.command_plugins[msg_type] = plugins = {}
            
            if not command_plugins:
                continue
            
            for command_plugin in command_plugins:
                split_path = command_plugin['path'].split('.')
                
                plugin_name = split_path.pop()
                module_path = '.'.join(split_path)
                
                module = __import__('%s.%s' % (plugin_path, module_path))
                for part in split_path:
                    module = getattr(module, part)
                    
                commands = tuple(command_plugin['commands'])
                plugins[commands] = getattr(module, plugin_name)(self)
        
        event_plugins = {}
        for event in settings['event_plugins']:
            name = getattr(irc.Events, event['name'])
            plugins = []
            for plugin in event['plugins']:
                split_path = plugin.split('.')
                
                plugin_name = split_path.pop()
                module_path = '.'.join(split_path)
            
                module = __import__('%s.%s' % (plugin_path, module_path))
                for part in split_path:
                    module = getattr(module, part)
                
                plugins.append(getattr(module, plugin_name)(self))
            
            event_plugins[name] = plugins
                
        super(IRCBot, self).__init__(servers, event_plugins)
        
        self.command_prefix = settings['command_prefix']
        self.version = settings['version_string']
    
    def on_welcome(self, connection, source, target, message):
        initial_channels = self.initial_channels[connection.server]
        if initial_channels:
            self.join(connection, *initial_channels)
    
    def is_admin(self, server, nick):
        return nick in self.admins[server]
    
    def get_version(self):
        return self.version
    
    def process_message(self, connection, source, target, message, pubmsg=True):
        if message[0] == self.command_prefix:
            tokens = message[1:].split(' ')
            command, args = tokens[0], tokens[1:]
            
            both = self.command_plugins['BOTH'].iteritems()
            if pubmsg:
                either = self.command_plugins['PUBMSG'].iteritems()
            else:
                either = self.command_plugins['PRIVMSG'].iteritems()
            
            for commands, plugin in itertools.chain(both, either):
                if command in commands:
                    plugin.process(connection, source, target, args)
    
    def on_privmsg(self, connection, source, target, message):
        process = Process(target=self.process_message,
                            args=(connection, source, target, message), kwargs={'pubmsg': False})
        process.start()
    
    def on_pubmsg(self, connection, source, target, message):
        process = Process(target=self.process_message,
                            args=(connection, source, target, message), kwargs={'pubmsg': True})
        process.start()
    
