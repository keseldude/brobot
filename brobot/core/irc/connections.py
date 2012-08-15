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
from time import sleep
from utils import parse_irc_line
from threading import Lock
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
        self.connection_locks = {}
        self.event_manager = event_manager
        self.queue = []
        self._running = False
    
    @property
    def running(self):
        return self._running
    
    def register(self, connection):
        """Registers a connection to the ConnectionManager and hooks in the
        CONNECT event."""
        self._running = True
        self.connections[connection.socket] = connection
        self.connection_locks[connection.socket] = Lock()
        self.event_manager.hook(Events.CONNECT, connection)
    
    def process(self, timeout=0.2):
        keys = self.connections.keys()
        if not keys:
            sleep(timeout)
            return
        try:
            in_sockets, _, _ = \
                select.select(keys, [], [], timeout)
        except socket.error as error:
            log.debug(unicode(error))
            for sock, connection in self.connections.items():
                if not connection.connected:
                    del self.connections[sock]
                    del self.connection_locks[sock]
        except select.error:
            pass
        else:
            for sock in in_sockets:
                try:
                    connection = self.connections[sock]
                except KeyError:
                    continue
                if connection.socket is None:
                    del self.connections[sock]
                    del self.connection_locks[sock]
                else:
                    with self.connection_locks[sock]:
                        connection.process(self.event_manager)
    
    def disconnect(self, connection, message=u''):
        """Closes a connection with an optional message."""
        if connection.socket is not None and\
                connection.socket in self.connections:
            lock = self.connection_locks[connection.socket]
            del self.connection_locks[connection.socket]
            del self.connections[connection.socket]
            with lock:
                connection.disconnect(message)
    
    def exit(self, message=u''):
        """Closes all connections with an optional message."""
        if self._running:
            for connection in self.connections.values():
                self.disconnect(connection, message)
            self._running = False
    

class Connection(object):
    """The lowest level of the IRC library. Connection takes care of connecting,
    disconnecting, parsing messages, sending messages, and hooking into IRC
    events."""
    def __init__(self, server):
        self._connected = False
        self._welcomed = False
        self.server = server
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.server.use_ssl:
            if ssl is None:
                error_msg = u'SSL connections require the python ssl library.'
                log.critical(error_msg)
                raise IRCError(error_msg)
            self._socket = ssl.wrap_socket(self._socket)
        self.prev_line = ''
    
    def set_welcomed(self):
        self._welcomed = True
    
    @property
    def welcomed(self):
        return self._welcomed
    
    def connect(self):
        """Connects to the server specified by the Connection object."""
        try:
            self._socket.connect((self.server.host, self.server.port))
        except socket.error:
            log.error(u'Unable to connect. Probably not connected to the \
internet.')
            try:
                self._socket.close()
            except socket.error as error:
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
            except socket.error as error:
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
        except socket.error as error:
            log.error(unicode(error))
            self.disconnect('Connection reset by peer')
        else:
            if not data:
                log.error(u'No data received from server.')
                self.disconnect('Connection reset by peer')
            else:
                # I'm a little worried that the \r\n convention isn't strictly followed
                # lines = (self.prev_line + data).split('\r\n')
                lines = [s.strip() for s in (self.prev_line + data).split('\n')]
                self.prev_line = lines.pop()
                
                for line in lines:
                    if not line:
                        continue
                    line_info = parse_irc_line(self.server, line)
                    command = line_info['command']
                    del line_info['command']
                    if command != Events.PONG:
                        log.debug(unicode(line, 'utf-8'))
                    try:
                        event_manager.hook(command, self, line_info)
                    except IRCError as e:
                        log.error('%s resulted in IRCError "%s".' % (line_info, e))

    def send(self, message):
        """Sends a message to the server."""
        if self._socket is None:
            raise IRCError('No socket :(')
        
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        
        try:
            self._socket.send(message + '\r\n')
        except socket.error as error:
            log.error(unicode(error))
            raise IRCError(u'Unable to send message.')
    
