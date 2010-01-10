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

from core import bot
import re
import urllib

from BeautifulSoup import BeautifulSoup

class URITitlePlugin(bot.EventPlugin):
    URI_RE = re.compile(r'https?://[A-Za-z0-9\-\._/&%#=?+]+')
    def __init__(self, ircbot):
        super(URITitlePlugin, self).__init__(ircbot, 'uri-title')
    
    def get_title(self, uri):
        try:
            connected_uri = urllib.urlopen(uri)
        except IOError:
            pass
        else:
            content_type = connected_uri.info()['Content-Type']
            if content_type.startswith('text/html'):
                soup = BeautifulSoup(connected_uri)
                
                if soup.title is not None:
                    title = BeautifulSoup(u' '.join(soup.title.string.split()), convertEntities=BeautifulSoup.XHTML_ENTITIES)
                    return unicode(title)
        return ''
    
    def process(self, connection, source='', target='', args=[], message=''):
        for uri in self.URI_RE.findall(message):
            title = self.get_title(uri)
            
            if title:
                self.ircbot.privmsg(connection, target, '\x02Title:\x02 ' + title)
    
