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
import re
import urllib
import logging
import lxml.html

log = logging.getLogger(__name__)

class FirefoxURLopener(urllib.FancyURLopener):
    version = "Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.2.9) \
Gecko/20100913 Firefox/3.6.9"

urllib._urlopener = FirefoxURLopener()

class URITitlePlugin(bot.EventPlugin):
    name = 'uri-title'
    URI_RE = re.compile(r'https?://[A-Za-z0-9:\-\.\'_/&%#!=?,+*;~\$\[\]]+')
    def get_title(self, uri):
        try:
            t = lxml.html.parse(uri)
        except IOError as e:
            log.error(unicode(e))
            return None
        title = t.find('.//title')
        return getattr(title, 'text', None)
    
    def process(self, connection, source='', target='', message=''):
        for uri in self.URI_RE.findall(message):
            title = self.get_title(uri)
            
            if title is not None:
                self.ircbot.privmsg(connection, target, '\x02Title:\x02 ' + \
                                    title.encode('utf-8'))
    
