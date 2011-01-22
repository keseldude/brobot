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

from events import Events
from structures import User
import socket, select
import logging

log = logging.getLogger(__name__)

try:
    import ssl
except ImportError:
    log.warning(u'Unable to import ssl module')
    ssl = None

class IRCError(Exception):
    """The error to use for low level IRC problems."""
    pass

class ConnectionManager(object):
    """Manages all connections made."""
    def __init__(self, event_manager):
        self.connections = {} # socket -> connection
        self.event_manager = event_manager
    
    def register(self, connection):
        """Registers a connection to the ConnectionManager and hooks in the
        CONNECT event."""
        self.connections[connection.socket] = connection
        self.event_manager.hook(Events.CONNECT, connection)
    
    def process(self, timeout=0.2):
        try:
            in_sockets, _, _ = \
                select.select(self.connections.keys(), [], [], timeout)
        except socket.error, error:
            log.debug(unicode(error))
            for sock, connection in self.connections.items():
                if not connection.connected:
                    del self.connections[sock]
        except (select.error, KeyboardInterrupt):
            self.exit(u'Bye!')
        else:
            for sock in in_sockets:
                self.connections[sock].process(self.event_manager)
    
    def disconnect(self, connection, message=u''):
        """Closes a connection with an optional message."""
        del self.connections[connection.socket]
        connection.disconnect(message)
    
    def exit(self, message=u''):
        """Closes all connections with an optional message."""
        if self.running:
            for connection in self.connections.values():
                del self.connections[connection.socket]
                connection.disconnect(message)
    
    @property
    def running(self):
        return len(self.connections) > 0
    

class Connection(object):
    """The lowest level of the IRC library. Connection takes care of connecting,
    disconnecting, parsing messages, sending messages, and hooking into IRC
    events."""
    def __init__(self, server):
        self._connected = False
        self.server = server
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.server.use_ssl:
            if ssl is None:
                error_msg = u'SSL connections require the python ssl library.'
                log.critical(error_msg)
                raise IRCError(error_msg)
            self._socket = ssl.wrap_socket(self._socket)
        self.prev_line = ''
    
    def connect(self):
        """Connects to the server specified by the Connection object."""
        try:
            self._socket.connect((self.server.host, self.server.port))
        except socket.error, error:
            log.error(unicode(error))
            try:
                self._socket.close()
            except socket.error, error:
                log.critical(unicode(error))
            
            return False
        
        self._connected = True
        
        return True
    
    def disconnect(self, message=u''):
        """Disconnects from the server with an optional message."""
        if not self._connected or self._socket is None:
            return
        try:
            if message:
                self.send(u'QUIT :' + message)
            else:
                self.send(u'QUIT')
        except IRCError:
            pass
        else:
            try:
                self._socket.close()
            except socket.error, error:
                log.critical(unicode(error))
                raise IRCError(error)
        
        self._socket = None
        self._connected = False
    
    @property
    def connected(self):
        return self._connected
    
    @property
    def socket(self):
        return self._socket
    
    def process(self, event_manager):
        """Processes new data received from the IRC server."""
        try:
            data = self._socket.recv(4096)
        except socket.error, error:
            log.error(unicode(error))
            self.disconnect('Connection reset by peer')
        else:
            if not data:
                log.error(u'No data received from server.')
                self.disconnect('Connection reset by peer')
            else:
                lines = (self.prev_line + data).split('\r\n')
                self.prev_line = lines.pop()
                
                for line in lines:
                    if not line:
                        continue
                    
                    log.debug(unicode(line, 'utf-8'))
                    
                    line_info = self._line_info(line)
                    command = line_info['command']
                    del line_info['command']
                    
                    event_manager.hook(command, self, line_info)
    
    def _line_info(self, line):
        """Line format:
        [:][<source>] <command> [<target>] [<args> ...][ :<message>]"""
        raw_source, command, target, args, message = '', '', '', [], ''
        
        split_line = line.split(' :', 1)
        split_line_len = len(split_line)
        if split_line_len == 1:
            if line.startswith(':'):
                split_prefix = line[1:].split()
            else:
                split_prefix = line.split()
        elif split_line_len == 2:
            irc_protocol_prefix, message = split_line
            if irc_protocol_prefix.startswith(':'):
                split_prefix = irc_protocol_prefix[1:].split()
            else:
                split_prefix = irc_protocol_prefix.split()
        
        prefix_len = len(split_prefix)
        
        if prefix_len == 3:
            raw_source, command, target = split_prefix
            
            if not self.server.actual_host:
                self.server.actual_host = raw_source
        elif prefix_len == 1:
            command = split_prefix[0]
        elif prefix_len == 2:
            raw_source, command = split_prefix
        elif prefix_len > 3:
            (raw_source, command, target), args = (split_prefix[:3],
                                                   split_prefix[3:])
        
        if not raw_source or raw_source == self.server.actual_host:
            source = raw_source
        else:
            source = User.parse_user(raw_source)
        
        is_channel = target and target[0] in '#&+!'
        
        if command == Events.PRIVMSG and is_channel:
            command = Events.PUBMSG
        elif command == Events.MODE and not is_channel:
            command = Events.UMODE
        elif command == Events.NOTICE:
            if is_channel:
                command = Events.PUBNOTICE
            else:
                command = Events.PRIVNOTICE
        
        if self.server.actual_nick and target == self.server.actual_nick:
            target = User.parse_user(target)
        
        line_info = {
            'source': source,
            'command': command,
            'target': target,
            'args': args,
            'message': message.decode('utf-8')
        }
        
        for name, value in line_info.items():
            if not value:
                del line_info[name]
        
        return line_info
    
    def send(self, message):
        """Sends a message to the server."""
        if self._socket is None:
            raise IRCError('No socket :(')
        
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        
        try:
            self._socket.send(message + '\r\n')
        except socket.error, error:
            log.error(unicode(error))
            raise IRCError(u'Unable to send message.')
    
