#===============================================================================
# brobot
# Copyright (C) 2012  Michael Keselman
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

def parse_irc_line(server, line):
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
        
        if not server.actual_host:
            server.actual_host = raw_source
    elif prefix_len == 1:
        command = split_prefix[0]
    elif prefix_len == 2:
        raw_source, command = split_prefix
    elif prefix_len > 3:
        (raw_source, command, target), args = (split_prefix[:3],
                                               split_prefix[3:])
    
    if not raw_source or raw_source == server.actual_host:
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
    
    if server.actual_nick and target == server.actual_nick:
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
    
