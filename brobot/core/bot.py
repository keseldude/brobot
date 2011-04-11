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

from irc.clients import Client
from irc.structures import Server
from irc.events import Events
from irc.connections import IRCError
from threading import Thread
import itertools
import logging
import os

log = logging.getLogger(__name__)

class Plugin(object):
    """Abstract class, which initializes every plugin to have the essentials:
    
    * a name
    * a link to the ircbot
    * the path to the common shelf (for serialized objects).
    """
    name = 'unnamed'
    admin = False
    def __init__(self, ircbot):
        self.ircbot = ircbot
        self.shelf_path = os.path.join(ircbot.data_path, 'shelf.db')
        try:
            self.load()
        except NotImplementedError:
            pass
    
    def load(self):
        raise NotImplementedError
    

class CommandPlugin(Plugin):
    """Abstract Plugin to be used for commands."""
    class Action(object):
        PRIVMSG = staticmethod(lambda bot: bot.privmsg)
        NOTICE  = staticmethod(lambda bot: bot.notice)
    
    def _process(self, connection, source, target, args):
        result = self.process(connection, source, target, args)
        if not result:
            return
        
        try:
            action = result['action'](self.ircbot)
            target = result['target']
            message = result['message']
        except KeyError:
            log.error(u'Invalid plugin response.')
        else:
            for line in message:
                try:
                    action(connection, target, line)
                except IRCError as e:
                    log.error(e)
                except Exception:
                    pass
    
    def process(self, connection, source, target, args):
        raise NotImplementedError
    

class EventPlugin(Plugin):
    """Abstract Plugin to be used for events."""
    def process(self, connection, source='', target='', args=None, message=''):
        raise NotImplementedError
    

class IRCBot(Client):
    """Functional implementation of Client, which serves as an IRC bot as
    opposed to a fully function client."""
    def __init__(self, settings):
        self.settings = settings
        
        self.data_path = os.path.join(settings['base_path'],
                                      settings['data_path'])
        if not os.path.exists(self.data_path):
            try:
                os.mkdir(self.data_path)
            except OSError:
                raise Exception('Unable to create data directory.')
        
        self._register_loggers()
        
        self.pid_path = os.path.join(self.data_path, settings['pid_filename'])
        self._save_pid(self.pid_path)
        
        self.admins = {}
        self.initial_channels = {}
        
        servers = []
        for server in settings['servers']:
            irc_server = Server(server['host'], server['port'], server['nick'],
                                name=server['name'], use_ssl=server['ssl'])
            servers.append(irc_server)
            self.admins[irc_server] = server['admins']
            self.initial_channels[irc_server] = server['channels']
        
        self.plugin_path = settings['plugin_path']
        
        event_plugins = {}
        for event in settings['event_plugins']:
            if 'plugins' not in event:
                continue
            
            name = getattr(Events, event['name'])
            plugins = []
            for plugin in event['plugins']:
                split_path = plugin.split('.')
                
                plugin_name = split_path.pop()
                module_path = '.'.join(split_path)
            
                module = __import__('%s.%s' % (self.plugin_path, module_path))
                reload(module)
                for part in split_path:
                    module = getattr(module, part)
                
                plugins.append(getattr(module, plugin_name)(self))
            
            event_plugins[name] = plugins
                
        super(IRCBot, self).__init__(servers, event_plugins)
        
        self.command_plugins = {}
        
        self.command_prefix = settings['command_prefix']
        self.version = settings['version_string']
        
        self._restart = False
    
    def _register_loggers(self):
        root_logger = logging.getLogger('')
        root_logger.setLevel(logging.DEBUG)
        
        fh = logging.FileHandler(os.path.join(self.data_path,
                                              self.settings['log_filename']),
                                 encoding='utf-8')
        fh_fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)-8s: \
%(message)s")
        fh.setFormatter(fh_fmt)
        if self.settings['debug']:
            ch = logging.StreamHandler()
            
            ch_fmt = logging.Formatter("%(levelname)-8s - %(message)s")
            
            ch.setFormatter(ch_fmt)
            ch.setLevel(logging.DEBUG)
            root_logger.addHandler(ch)
            fh.setLevel(logging.DEBUG)
        else:
            fh.setLevel(logging.INFO)
        
        root_logger.addHandler(fh)
    
    def _save_pid(self, pid_path):
        pid = os.getpid()
        with open(pid_path, 'w') as pidfile:
            pidfile.write(str(pid))
    
    def _register_command_plugins(self):
        items = self.settings['command_plugins'].iteritems()
        for msg_type, command_plugins in items:
            self.command_plugins[msg_type] = plugins = {}
            
            if command_plugins is None:
                continue
            
            for command_plugin in command_plugins:
                split_path = command_plugin['path'].split('.')
                
                plugin_name = split_path.pop()
                module_path = '.'.join(split_path)
                
                module = __import__('%s.%s' % (self.plugin_path, module_path))
                reload(module)
                for part in split_path:
                    module = getattr(module, part)
                    
                commands = tuple(command_plugin['commands'])
                plugins[commands] = getattr(module, plugin_name)(self)
    
    def start(self):
        super(IRCBot, self).start()
        return self._restart
    
    def restart(self):
        self._restart = True
        self.exit(message=u'Restarting!')
    
    def register_command_plugin(self, command, plugin):
        both = self.command_plugins['BOTH']
        for commands in both.iterkeys():
            if command in commands:
                return False
        self.command_plugins['BOTH'][(command,)] = plugin(self)
        
        return True
    
    def unregister_command_plugin(self, command):
        commands = (command,)
        both = self.command_plugins['BOTH']
        for cmds in both.iterkeys():
            if cmds == commands:
                del both[cmds]
                return True
        return False
    
    def on_connect(self, connection):
        pass
    
    def on_welcome(self, connection, source, target, message):
        initial_channels = self.initial_channels[connection.server]
        if initial_channels:
            self.join(connection, *initial_channels)
    
    def on_initial_connect(self):
        self._register_command_plugins()
    
    def is_admin(self, server, nick):
        """Returns whether a given nick is one of the administrators of the
        bot."""
        return nick in self.admins[server]
    
    def get_version(self):
        """Returns the version of the bot."""
        return self.version
    
    def process_message(self, connection, source, target, message, is_pubmsg):
        """Processes a message, determining whether it is a bot command, and
        taking action if it is."""
        if message[0] == self.command_prefix:
            if message[1:2] == u' ':
                command = u' '
                args = message[2:].strip().split(u' ')
            else:
                tokens = message[1:].strip().split(u' ')
                command, args = tokens[0], tokens[1:]
            
            both = self.command_plugins['BOTH'].iteritems()
            if is_pubmsg:
                either = self.command_plugins['PUBMSG'].iteritems()
            else:
                either = self.command_plugins['PRIVMSG'].iteritems()
            
            for commands, plugin in itertools.chain(both, either):
                if command in commands:
                    plugin._process(connection, source, target, args)
                    break
    
    def _on_msg(self, connection, source, target, message, is_pubmsg):
        process = Thread(target=self.process_message,
                            args=(connection, source, target, message,
                                  is_pubmsg))
        process.daemon = True
        process.start()
    
    def on_privmsg(self, connection, source, target, message):
        self._on_msg(connection, source, source.nick, message, False)
    
    def on_pubmsg(self, connection, source, target, message):
        self._on_msg(connection, source, target, message, True)
    
