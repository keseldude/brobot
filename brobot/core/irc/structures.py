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
Contains the core structures needed for IRC.
"""

from threading import Lock

class Server(object):
    """An IRC server represenation, which stores the host, port, and nick of the
    user connected. Supports ssl (soon)."""
    def __init__(self, host, port, nick, use_ssl=False):
        self.host = host
        self.port = port
        self.nick = nick
        self.use_ssl = use_ssl
        
        self.actual_host = ''
        self.actual_nick = ''
    
    def __eq__(self, other):
        return self.actual_host == other.actual_host and\
                self.port == other.port and\
                self.actual_nick == other.actual_nick
    

class Channel(object):
    """An IRC channel representation."""
    def __init__(self, server, name, users=None, modes=None):
        self.server = server
        self.name = name.lower()
        
        self.user_lock = Lock()
        self.mode_lock = Lock()
        
        if users is None:
            self.users = []
        
        if modes is None:
            self.modes = []
    
    def __eq__(self, other):
        return self.server == other.server and self.name == other.name
    
    def __repr__(self):
        return self.name
    
    def in_channel(self, nick):
        user = User.channel_user(nick)
        return user in self.users
    
    def add_user(self, user):
        """Adds a user to the list of users if it is not already there."""
        with self.user_lock:
            if user not in self.users:
                self.users.append(user)
    
    def remove_user(self, user):
        """Tries to remove a user from the set of users in the channel, and
        fails silently."""
        with self.user_lock:
            try:
                self.users.remove(user)
            except ValueError:
                pass
    
    def find_user(self, nick):
        search_user = User.channel_user(nick)
        for user in self.users:
            if user == search_user:
                return user
        return None
    
    def add_mode(self, mode):
        """Adds a mode to the list of modes if it is not already there."""
        with self.mode_lock:
            if mode not in self.modes:
                self.modes.append(mode)
    
    def remove_mode(self, mode):
        """Tries to remove a mode from the set of modes in the channel, and
        fails silently."""
        with self.mode_lock:
            try:
                self.modes.remove(mode)
            except ValueError:
                pass
    

class Mode(object):
    """An IRC mode representation, which stores the mode character, the
    parameter, and whether it is on."""
    SWITCH = ('-', '+')
    def __init__(self, character, param='', on=True):
        self.character = character
        self.param = param
        self.on = on
    
    def __eq__(self, other):
        return self.character == other.character
    
    def __repr__(self):
        mode = '%s%s' % (self.SWITCH[self.on], self.character)
        if self.param:
            mode += ' %s' % self.param
        
        return mode
    
    @staticmethod
    def parse_modes(modes, mode_args):
        if not modes.startswith('+') and not modes.startswith('-'):
            return []
        
        on = modes[0] == '+'
        
        if '+' not in modes:
            on_modes = ''
            off_modes = modes[1:]
        elif '-' not in modes:
            on_modes = modes[1:]
            off_modes = ''
        else:
            first_pass = modes.split('+')
            if first_pass[0]:
                second_pass = first_pass[0].split('-')
                on_modes, off_modes = first_pass[1], second_pass[1]
            else:
                second_pass = first_pass[1].split('-')
                on_modes, off_modes = second_pass
        
        arg_index = len(on_modes) + len(off_modes) - len(mode_args)
        
        l = []
        i = 0
        
        if on:
            iterlist = (on_modes, off_modes)
        else:
            iterlist = (off_modes, on_modes)
        
        for j, mode_list in enumerate(iterlist):
            switched_on = bool((j + on) % 2)
            for mode in mode_list:
                if i < arg_index:
                    l.append(Mode(mode, on=switched_on))
                else:
                    l.append(Mode(mode, param=mode_args[i], on=switched_on))
                i += 1
        
        return l
    

class User(object):
    """An IRC user represenation, storing nick, username, host, and channel
    status."""
    NORMAL = ' '
    VOICE = '+'
    HALFOP = '%'
    OP = '@'
    PROTECTED = '&'
    FOUNDER = '~'
    
    STATUSES = {
        NORMAL: 1,
        VOICE: 2,
        HALFOP: 4,
        OP: 8,
        PROTECTED: 16,
        FOUNDER: 32
    }
    
    MODES = {
        'v': VOICE,
        'h': HALFOP,
        'o': OP,
        'a': PROTECTED,
        'q': FOUNDER
    }
    
    def __init__(self, nick, username, host, status):
        self.nick = nick.lower()
        self.username = username
        self.host = host
        
        if status in self.STATUSES:
            self.status = self.STATUSES[status]
        else:
            self.status = self.STATUSES[self.NORMAL]
    
    def __eq__(self, other):
        return self.nick == other.nick and \
                self.username == other.username and \
                self.host == other.host
    
    def __repr__(self):
        return self.nick
    
    def add_mode(self, mode):
        status = self.STATUSES[self.MODES[mode.character]]
        self.status |= status
    
    def remove_mode(self, mode):
        status = self.STATUSES[self.MODES[mode.character]]
        self.status -= status
    
    @staticmethod
    def channel_user(nick):
        return User(nick, '', '', User.NORMAL)
    
    @staticmethod
    def parse_user(user):
        """Helper function that parses user information into a User object."""
        username, host = '', ''
        if user[0] in User.STATUSES:
            status, nick = user[0], user[1:]
        else:
            status = User.NORMAL
            split_user = user.split('@')
            
            if len(split_user) == 1:
                nick = split_user[0]
            else:
                info, host = split_user
                nick, username = info.split('!')
        
        return User(nick, username, host, status)
    
