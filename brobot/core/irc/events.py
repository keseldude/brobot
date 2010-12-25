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

class EventManager(object):
    """Manages IRC event actions."""
    
    EVENT_ARGS = ('source', 'target', 'args', 'message')
    
    def __init__(self, event_hooks):
        self.event_hooks = event_hooks
    
    def hook(self, event, connection, kwargs=None):
        if event in self.event_hooks:
            event_hook = self.event_hooks[event]
            if kwargs is None:
                kwargs = {}
            args = (kwargs.get(arg, '') for arg in self.EVENT_ARGS \
                    if getattr(event_hook, arg))
            event_hook.function(connection, *args)
    

class EventHook(object):
    """Communication object that describes which action to take for a given IRC
    event."""
    def __init__(self, function, source=False, target=False, args=False, message=False):
        self.function = function
        self.source = source
        self.target = target
        self.args = args
        self.message = message
    

class Events(object):
    CONNECT = 'CONNECT'
    PING = 'PING'
    MODE = 'MODE'
    UMODE = 'UMODE'
    JOIN = 'JOIN'
    PART = 'PART'
    QUIT = 'QUIT'
    PRIVMSG = 'PRIVMSG'
    PUBMSG = 'PUBMSG'
    NOTICE = 'NOTICE'
    PUBNOTICE = 'PUBNOTICE'
    PRIVNOTICE = 'PRIVNOTICE'
    ERROR = 'ERROR'
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
