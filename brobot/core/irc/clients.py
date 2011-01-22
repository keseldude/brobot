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

"""
Contains mid-level building blocks for an IRC client. This is really the bridge
between the low-level connections module and the high level client that someone
using this library would write.
"""

from events import Events, EventManager, EventHook
from connections import ConnectionManager, Connection, IRCError
from structures import Channel, Server, User, Mode
from datetime import datetime
from threading import Lock, Thread
import logging
import time

log = logging.getLogger(__name__)

class PluginEventManager(EventManager):
    """An extension of EventManager that allows for plugins to hook into IRC
    events."""
    def __init__(self, event_hooks, event_plugins):
        super(PluginEventManager, self).__init__(event_hooks)
        
        self.event_plugins = event_plugins
    
    def hook(self, event, connection, kwargs=None):
        """Still performs the regular event hooks, and afterward, the plugin
        hooks."""
        super(PluginEventManager, self).hook(event, connection, kwargs)
        
        if event in self.event_plugins:
            for plugin in self.event_plugins[event]:
                plugin.process(connection, **kwargs)
    
class Client(object):
    """The base IRC Client, which wraps a ConnectionManager and provides an
    interface to low level connection functions. It can be extended to make a
    full IRC client or an IRC bot."""
    def __init__(self, servers, event_plugins=None):
        self.channels = []
        self._servers = servers
        self.pinged = False
        
        if event_plugins is None:
            event_plugins = {}
        
        self.connection_manager = ConnectionManager(PluginEventManager({
            Events.CONNECT: EventHook(self._on_connect),
            Events.RPL_WELCOME: EventHook(self._on_welcome, source=True,
                                          target=True, message=True),
            Events.PING: EventHook(self._on_ping, message=True),
            Events.MODE: EventHook(self._on_mode, source=True, target=True,
                                   args=True),
            Events.UMODE: EventHook(self._on_umode, source=True, target=True,
                                    message=True),
            Events.JOIN: EventHook(self._on_join, source=True, message=True),
            Events.PART: EventHook(self._on_part, source=True, target=True,
                                   message=True),
            Events.QUIT: EventHook(self._on_quit, source=True, message=True),
            Events.RPL_NAMEREPLY: EventHook(self._on_name_reply, source=True,
                                            target=True, args=True,
                                            message=True),
            Events.PRIVMSG: EventHook(self._on_privmsg, source=True,
                                      target=True, message=True),
            Events.PUBMSG: EventHook(self._on_pubmsg, source=True, target=True,
                                     message=True),
            Events.RPL_CHANNELMODEIS: EventHook(self._on_channel_mode,
                                                source=True, target=True,
                                                args=True),
            Events.ERR_NICKNAMEINUSE: EventHook(self.on_nickname_in_use),
            Events.ERROR: EventHook(self._on_error, message=True)
        }, event_plugins))
        
        self.process_lock = Lock()
    
    def start(self):
        """Starts the Client by first connecting to all given servers and then
        starting the main loop."""
        for server in self._servers:
            Thread(target=self._connect, args=(server,)).start()
        
        try:
            self.on_initial_connect()
        except NotImplementedError:
            pass
        
        while self.connection_manager.running:
            with self.process_lock:
                self.connection_manager.process()
    
    def _connect(self, server, tries=5):
        """Performs a connection to the server by creating a Connection object,
        connecting it, and then registering the new Connection with the
        ConnectionManager."""
        server.reset()
        
        for _ in xrange(tries):
            connection = Connection(server)
            if connection.connect():
                self.connection_manager.register(connection)
                return
            time.sleep(30)
    
    def on_initial_connect(self):
        """Function performed after all servers have been connected."""
        raise NotImplementedError
    
    def exit(self, message=u'Bye!'):
        """Disconnects from every connection in the ConnectionManager with the
        given QUIT message."""
        with self.process_lock:
            self.connection_manager.exit(message)
    
    def get_server_by_name(self, name):
        for server in self._servers:
            if server.name == name:
                return server
        return None
    
    def get_server_channels(self, server):
        for channel in self.channels:
            if channel.server == server:
                yield channel
    
    def find_channel(self, server, name):
        """Searches for a Channel based on the server and the name. Returns
        None if the Channel is not found."""
        search_channel = Channel(server, name)
        for channel in self.channels:
            if search_channel == channel:
                return channel
        return None
    
    def remove_channel(self, server, name):
        """Tries to remove a Channel based on the server and the name, and fails
        silently."""
        channel = Channel(server, name)
        try:
            self.channels.remove(channel)
        except ValueError:
            log.debug(u"Channel `%s' not in channels." % name)
    
    def find_connection(self, server):
        """Searches for a Connection based on the server and compares only the
        host of the server. Returns None if the Connection is not found."""
        for connection in self.connection_manager.connections.itervalues():
            if connection.server.host == server.host:
                return connection
        return None
    
    def connect(self, host, port, nick, use_ssl=False):
        """Used for connecting to a server not given when creating the Client
        object."""
        server = Server(host, port, nick, use_ssl)
        self._connect(server)
    
    def nick(self, connection, new_nick):
        """Changes the nick in the given connection."""
        connection.send('NICK ' + new_nick)
    
    def mode(self, connection, target, mode=None):
        """Performs the IRC MODE command."""
        mode_message = 'MODE %s' % target
        if mode is not None:
            mode_message += ' %s' % mode
        connection.send(mode_message)
    
    def privmsg(self, connection, target, message):
        """Sends a PRIVMSG to a target in the given connection."""
        connection.send('PRIVMSG %s :%s' % (target, message))
    
    def notice(self, connection, target, message):
        """Sends a NOTICE to a target in the given connection."""
        connection.send('NOTICE %s :%s' % (target, message))
    
    def ctcp_reply(self, connection, target, command, reply):
        """Sends a CTCP reply to a target in a given connection."""
        self.notice(connection, target, '\x01%s %s\x01' % (command, reply))
    
    def join(self, connection, *channels):
        """Makes the client join a bunch of channels. Example password protected
        channel argument: '#mathematics love' where 'love' is the password."""
        connection.send('JOIN ' + ','.join(channels))
    
    def part(self, connection, *channels):
        """Makes the client part from a bunch of channels."""
        connection.send('PART ' + ','.join(channels))
    
    def kick(self, connection, channel, user, reason=''):
        """Kicks a user from a channel in a given connection for a given
        reason."""
        connection.send('KICK %s %s :%s' % (channel, user, reason))
    
    def quit(self, connection, message=u''):
        """Disconnects the given connection with the given message. This is
        better than just quitting because it also cleans things up with the
        connection manager."""
        with self.process_lock:
            self.connection_manager.disconnect(connection, message)
    
    def on_connect(self, connection):
        raise NotImplementedError
    
    def _on_connect(self, connection):
        connection.send('NICK ' + connection.server.nick)
        connection.send('USER %s 0 * :%s' % (connection.server.nick,
                                             connection.server.nick))
        
        try:
            self.on_connect(connection)
        except NotImplementedError:
            pass
    
    def on_welcome(self, connection, source, target, message):
        raise NotImplementedError
    
    def _on_welcome(self, connection, source, target, message):
        connection.server.actual_nick = target
        try:
            self.on_welcome(connection, source, target, message)
        except NotImplementedError:
            pass
    
    def on_nickname_in_use(self, connection):
        connection.server.nick = connection.server.nick + '_'
        self._on_connect(connection)
    
    def _on_join(self, connection, source, message):
        if source.nick == connection.server.actual_nick:
            channel = Channel(connection.server, message)
            self.channels.append(channel)

            self.mode(connection, channel)
        else:
            channel = self.find_channel(connection.server, message)
            if channel is not None:
                channel.add_user(User(source.nick, '', '', User.NORMAL))
    
    def _on_name_reply(self, connection, source, target, args, message):
        channel_name = args[-1]
        
        channel = self.find_channel(connection.server, channel_name)
        if channel is not None:
            for user in message.split():
                channel.add_user(User.parse_user(user))
    
    def _on_part(self, connection, source, target, message):
        if source.nick == connection.server.actual_nick:
            self.remove_channel(connection.server, target)
        else:
            channel = self.find_channel(connection.server, target)
            if channel is not None:
                channel.remove_user(User(source.nick, '', '', User.NORMAL))
    
    def _on_quit(self, connection, source, message):
        user = User.channel_user(source.nick)
        for channel in self.get_server_channels(connection.server):
            channel.remove_user(user)
    
    def on_privmsg(self, connection, source, target, message):
        raise NotImplementedError
    
    def _on_privmsg(self, connection, source, target, message):
        if message[0] == '\x01' and message[-1] == '\x01':
            self._on_ctcp(connection, source, message[1:-1])
        else:
            try:
                self.on_privmsg(connection, source, target, message)
            except NotImplementedError:
                pass
    
    def on_pubmsg(self, connection, source, target, message):
        raise NotImplementedError
    
    def _on_pubmsg(self, connection, source, target, message):
        try:
            self.on_pubmsg(connection, source, target, message)
        except NotImplementedError:
            pass
    
    def _on_channel_mode(self, connection, source, target, args):
        (name, modes), mode_args = args[:2], args[2:]
        channel = self.find_channel(connection.server, name)
        if channel is not None:
            channel_modes = Mode.parse_modes(modes, mode_args)
            for mode in channel_modes:
                if mode.on:
                    channel.add_mode(mode)
                else:
                    channel.remove_mode(mode)
    
    def get_version(self):
        raise NotImplementedError
    
    def _on_ctcp(self, connection, source, message):
        command, arg = '', ''
        split_message = message.split(' ', 1)
        if len(split_message) > 1:
            command, arg = split_message
        else:
            command = split_message[0]
        
        reply = ''
        
        if command == 'VERSION':
            try:
                reply = self.get_version()
            except NotImplementedError:
                pass
        elif command == 'PING' and arg:
            reply = arg
        elif command == 'TIME':
            reply = ':%s' % datetime.now().ctime()
        
        if reply:
            self.ctcp_reply(connection, source.nick, command, reply)
    
    def _on_mode(self, connection, source, target, args):
        channel = self.find_channel(connection.server, target)
        if channel is not None:
            modes, mode_args = args[0], args[1:]
            channel_modes = Mode.parse_modes(modes, mode_args)
            for mode in channel_modes:
                user = channel.find_user(mode.param)
                if user is not None:
                    if mode.on:
                        user.add_mode(mode)
                    else:
                        user.remove_mode(mode)
                else:
                    if mode.on:
                        channel.add_mode(mode)
                    else:
                        channel.remove_mode(mode)
    
    def _on_umode(self, connection, source, target, message):
        pass
    
    def _on_ping(self, connection, message):
        connection.send('PONG %s :%s' % (connection.server.actual_host,
                                         message))
    
    def _on_error(self, connection, message):
        if u'ping timeout' in message.lower():
            self._connect(connection.server)
        else:
            log.error(unicode(message))
    
