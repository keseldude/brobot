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

import socket
import select
from datetime import datetime

class IRCError(Exception):
    pass

class Server(object):
    """docstring for Server"""
    def __init__(self, host, port, nick, use_ssl=False):
        self.host = host
        self.port = port
        self.nick = nick
        self.use_ssl = use_ssl
        
        self.actual_host = ''
        self.actual_nick = ''
    

class User(object):
    def __init__(self, nick, username, host):
        self.nick = nick
        self.username = username
        self.host = host
    
    def __repr__(self):
        return self.nick
    
    @staticmethod
    def parse_user(user):
        username, host = '', ''
        split_user = user.split('@')
        if len(split_user) == 1:
            nick = split_user[0]
        else:
            info, host = split_user
            nick, username = info.split('!')
        
        return User(nick, username, host)
    

class EventManager(object):
    """docstring for EventManager"""
    EVENT_ARGS = ('source', 'target', 'args', 'message')
    def __init__(self, event_hooks):
        self.event_hooks = event_hooks
    
    def hook(self, event, connection, **kwargs):
        if event in self.event_hooks:
            event_hook = self.event_hooks[event]
            args = (kwargs[arg] for arg in self.EVENT_ARGS if getattr(event_hook, arg))
            event_hook.function(connection, *args)
    

class EventHook(object):
    def __init__(self, function, source=False, target=False, args=False, message=False):
        self.function = function
        self.source = source
        self.target = target
        self.args = args
        self.message = message
    

class ConnectionManager(object):
    """docstring for ConnectionManager"""
    def __init__(self, event_manager):
        self.connections = {} # socket -> connection
        self.event_manager = event_manager
    
    def register(self, connection):
        self.connections[connection.socket] = connection
        self.event_manager.hook(Events.CONNECT, connection)
    
    def process(self, timeout=0.2):
        try:
            in_sockets, out_sockets, err_sockets = \
                select.select(self.connections.keys(), [], [], timeout)
        except socket.error, error:
            for sock, connection in self.connections.items():
                if not connection.connected:
                    del self.connections[sock]
        except (select.error, KeyboardInterrupt):
            self.exit('Bye!')
        else:
            for sock in in_sockets:
                self.connections[sock].process(self.event_manager)
    
    def exit(self, message):
        for connection in self.connections.values():
            connection.disconnect(message)
    
    @property
    def running(self):
        return len(self.connections)

class Connection(object):
    """docstring for Connection"""
    def __init__(self, server):
        self._connected = False
        self.server = server
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.prev_line = ''
    
    def connect(self):
        try:
            self._socket.connect((self.server.host, self.server.port))
        except socket.error, error:
            self.disconnect()
            raise IRCError(error)
        else:
            self._connected = True
    
    def disconnect(self, message=''):
        if not self._connected or not self._socket:
            return
        
        try:
            self.send('QUIT :' + message)
            self._socket.close()
        except socket.error, error:
            raise IRCError(error)
        else:    
            self._socket = None
            self._connected = False
    
    @property
    def connected(self):
        return self._connected
    
    @property
    def socket(self):
        return self._socket
    
    def process(self, event_manager):
        try:
            data = self._socket.recv(4096)
        except socket.error, error:
            self.disconnect('Connection reset by peer')
        else:
            if not data:
                self.disconnect('Connection reset by peer')
            else:
                lines = (self.prev_line + data).split('\r\n')
                self.prev_line = lines.pop()
                
                for line in lines:
                    if not line:
                        continue
                    
                    print line
                    
                    line_info = self._line_info(line)
                    command = line_info['command']
                    del line_info['command']
                    
                    event_manager.hook(command, self, **line_info)
    
    def _line_info(self, line):
        """
        Line format:
        [:][<source>] <command> [<target>] [<args> ...][ :<message>]
        """
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
            command = split_prefix[1]
        elif prefix_len > 3:
            (raw_source, command, target), args = split_prefix[:3], split_prefix[3:]
        
        if not raw_source or raw_source == self.server.actual_host:
            source = raw_source
        else:
            source = User.parse_user(raw_source)
        
        is_channel = target and target[0] in '#&+!'
        
        if command == Events.PRIVMSG and is_channel:
            command = Events.PUBMSG
        elif command == Events.NOTICE:
            if is_channel:
                command = Events.PUBNOTICE
            else:
                command = Events.PRIVNOTICE
        
        if target == self.server.actual_nick:
            target = source
        
        line_info = {
            'source': source,
            'command': command,
            'target': target,
            'args': args,
            'message': message
        }
        
        for name, value in line_info.items():
            if not value:
                del line_info[name]
        
        return line_info
    
    def send(self, message):
        if self._socket is None:
            raise IRCError('No socket :(')
        
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        
        try:
            self._socket.send(message + '\r\n')
        except socket.error, error:
            raise IRCError('Unable to send message... something is seriously wrong.')
    

class PluginEventManager(EventManager):
    def __init__(self, event_hooks, event_plugins):
        super(PluginEventManager, self).__init__(event_hooks)
        
        self.event_plugins = event_plugins
    
    def hook(self, event, connection, **kwargs):
        super(PluginEventManager, self).hook(event, connection, **kwargs)
        
        if event in self.event_plugins:
            for plugin in self.event_plugins[event]:
                plugin.process(connection, **kwargs)

class Client(object):
    """docstring for Client"""
    def __init__(self, servers, event_plugins={}):
        self.channels = []
        
        self.connection_manager = ConnectionManager(PluginEventManager({
            Events.CONNECT: EventHook(self._on_connect),
            Events.RPL_WELCOME: EventHook(self._on_welcome, source=True, target=True, message=True),
            Events.PING: EventHook(self._on_ping, message=True),
            Events.MODE: EventHook(self._on_mode, source=True, target=True, message=True),
            Events.PRIVMSG: EventHook(self._on_privmsg, source=True, target=True, message=True),
            Events.PUBMSG: EventHook(self._on_pubmsg, source=True, target=True, message=True)
        }, event_plugins))
        
        for server in servers:
            self._connect(server)
    
    def _connect(self, server):
        """docstring for _connect"""
        connection = Connection(server)
        try:
            connection.connect()
        except IRCError, error:
            pass # log error message
        else:
            self.connection_manager.register(connection)
    
    def start(self):
        while self.connection_manager.running:
            self.connection_manager.process()
    
    def exit(self, message='Bye!'):
        self.connection_manager.exit(message)
    
    def connect(self, host, port, nick, use_ssl=False):
        server = Server(host, port, nick, use_ssl)
        self._connect(server)
    
    def nick(self, connection, new_nick):
        connection.send('NICK ' + new_nick)
    
    def privmsg(self, connection, target, message):
        connection.send('PRIVMSG %s :%s' % (target, message))
    
    def notice(self, connection, target, message):
        connection.send('NOTICE %s :%s' % (target, message))
    
    def ctcp_reply(self, connection, target, command, reply):
        self.notice(connection, target, '\x01%s %s\x01' % (command, reply))
    
    def join(self, connection, *channels):
        """
        Example password protected channel argument:
        '#mathematics love' where 'love' is the password.
        """
        connection.send('JOIN ' + ','.join(channels))
        for channel in channels:
            self.channels.append(channel.lower())
    
    def part(self, connection, *channels):
        connection.send('PART ' + ','.join(channels))
        for channel in channels:
            try:
                self.channels.remove(channel.lower())
            except ValueError:
                pass
    
    def kick(self, connection, channel, user, reason=''):
        connection.send('KICK %s %s :%s' % (channel, user, reason))
    
    def quit(self, connection, message=''):
        """
        Disconnecting just seems cleaner than simply sending QUIT
        and leaving the cleaning up to the connection manager.
        """
        connection.disconnect(message)
    
    def on_connect(self, connection):
        raise NotImplementedError
    
    def _on_connect(self, connection):
        connection.send('NICK ' + connection.server.nick)
        connection.send('USER %s 0 * :%s' % (connection.server.nick, connection.server.nick))
        
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
        elif command == 'PING':
            if arg:
                reply = arg
        elif command == 'TIME':
            reply = ':%s' % datetime.now().ctime()
        
        if reply:
            self.ctcp_reply(connection, source.nick, command, reply)
    
    def _on_mode(self, connection, source, target, message):
        pass
    
    def _on_ping(self, connection, message):
        connection.send('PONG %s :%s' % (connection.server.actual_host, message))
    

class Events:
    CONNECT = 'CONNECT'
    PING = 'PING'
    MODE = 'MODE'
    PRIVMSG = 'PRIVMSG'
    PUBMSG = 'PUBMSG'
    NOTICE = 'NOTICE'
    PUBNOTICE = 'PUBNOTICE'
    PRIVNOTICE = 'PRIVNOTICE'
    RPL_WELCOME = '001'
    RPL_YOURHOST = '002'
    RPL_CREATED = '003'
    RPL_MYINFO = '004'
    RPL_BOUNCE = '005'
    RPL_TRACELINK = '200'
    RPL_TRACECONNECTING = '201'
    RPL_TRACEHANDSHAKE = '202'
    RPL_TRACEUNKNOWN = '203'
    RPL_TRACEOPERATOR = '204'
    RPL_TRACEUSER = '205'
    RPL_TRACESERVER = '206'
    RPL_TRACESERVICE = '207'
    RPL_TRACENEWTYPE = '208'
    RPL_TRACECLASS = '209'
    RPL_TRACERECONNECT = '210'
    RPL_STATSLINKINFO = '211'
    RPL_STATSCOMMANDS = '212'
    RPL_ENDOFSTATS = '219'
    RPL_UMODEIS = '221'
    RPL_SERVLIST = '234'
    RPL_SERVLISTEND = '235'
    RPL_STATSUPTIME = '242'
    RPL_STATSOLINE = '243'
    RPL_LUSERCLIENT = '251'
    RPL_LUSEROP = '252'
    RPL_LUSERUNKNOWN = '253'
    RPL_LUSERCHANNELS = '254'
    RPL_LUSERME = '255'
    RPL_ADMINME = '256'
    RPL_ADMINLOC1 = '257'
    RPL_ADMINLOC2 = '258'
    RPL_ADMINEMAIL = '259'
    RPL_TRACELOG = '261'
    RPL_TRACEEND = '262'
    RPL_TRYAGAIN = '263'
    RPL_AWAY = '301'
    RPL_USERHOST = '302'
    RPL_ISON = '303'
    RPL_UNAWAY = '305'
    RPL_NOWAWAY = '306'
    RPL_WHOWASUSER = '314'
    RPL_ENDOFWHO = '315'
    RPL_LISTSTART = '321'
    RPL_LIST = '322'
    RPL_LISTEND = '323'
    RPL_CHANNELMODEIS = '324'
    RPL_UNIQOPIS = '325'
    RPL_NOTOPIC = '331'
    RPL_TOPIC = '332'
    RPL_INVITING = '341'
    RPL_SUMMONING = '342'
    RPL_INVITELIST = '346'
    RPL_ENDOFINVITELIST = '347'
    RPL_EXCEPTLIST = '348'
    RPL_ENDOFEXCEPTLIST = '349'
    RPL_VERSION = '351'
    RPL_WHOREPLY = '352'
    RPL_NAMEREPLY = '353'
    RPL_LINKS = '364'
    RPL_ENDOFLINKS = '365'
    RPL_ENDOFNAMES = '366'
    RPL_BANLIST = '367'
    RPL_ENDOFBANLIST = '368'
    RPL_INFO = '371'
    RPL_MOTD = '372'
    RPL_ENDOFINFO = '374'
    RPL_MOTDSTART = '375'
    RPL_ENDOFMOTD = '376'
    RPL_YOUREOPER = '381'
    RPL_REHASHING = '382'
    RPL_YOURESERVICE = '383'
    RPL_TIME = '391'
    RPL_USERSTART = '392'
    RPL_USERS = '393'
    RPL_ENDOFUSERS = '394'
    RPL_NOUSERS = '395'
    ERR_NOSUCHNICK = '401'
    ERR_NOSUCHSERVER = '402'
    ERR_NOSUCHCHANNEL = '403'
    ERR_CANNOTSENDTOCHAN = '404'
    ERR_TOOMANYCHANNELS = '405'
    ERR_WASNOSUCHNICK = '406'
    ERR_TOOMANYTARGETS = '407'
    ERR_NOSUCHSERVICE = '408'
    ERR_NOORIGIN = '409'
    ERR_NORECIPIENT = '411'
    ERR_NOTEXTTOSEND = '412'
    ERR_NOTOPLEVEL = '413'
    ERR_WILDTOPLEVEL = '414'
    ERR_BADMASK = '415'
    ERR_UNKNOWNCOMMAND = '421'
    ERR_NOMOTD = '422'
    ERR_NOADMININFO = '423'
    ERR_FILEERROR = '424'
    ERR_NONICKNAMEGIVEN = '431'
    ERR_ERRONEUSNICKNAME = '432'
    ERR_NICKNAMEINUSE = '433'
    ERR_NICKCOLLISION = '436'
    ERR_UNAVAILRESOURCE = '437'
    ERR_USERNOTINCHANNEL = '441'
    ERR_NOTONCHANNEL = '442'
    ERR_USERONCHANNEL = '443'
    ERR_NOLOGIN = '444'
    ERR_SUMMONDISABLED = '445'
    ERR_USERDISABLED = '446'
    ERR_NOTREGISTERED = '451'
    ERR_NEEDMOREPARAMS = '461'
    ERR_ALREADYREGISTERED = '462'
    ERR_NOPERMFORHOST = '463'
    ERR_PASSWDMISMATCH = '464'
    ERR_YOUREBANNEDCREEP = '465'
    ERR_YOUWILLBEBANNED = '466'
    ERR_KEYSET = '467'
    ERR_CHANNELISFULL = '471'
    ERR_UNKNOWNMODE = '472'
    ERR_INVITEONLYCHAN = '473'
    ERR_BANNEDFROMCHAN = '474'
    ERR_BADCHANNELKEY = '475'
    ERR_BADCHANMASK = '476'
    ERR_NOCHANMODES = '477'
    ERR_BANLISTFULL = '478'
    ERR_NOPRIVILEGES = '481'
    ERR_CHANOPRIVSNEED = '482'
    ERR_CANTKILLSERVER = '483'
    ERR_RESTRICTED = '484'
    ERR_UNIQOPRIVSNEEDED = '485'
    ERR_NOOPERHOST = '491'
    ERR_UMODEUNKNOWNFLAG = '501'
    ERR_USERSDONTMATCH = '502'
