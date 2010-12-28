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
from evaluator import evaluator

class PythonEvalPlugin(bot.CommandPlugin):
    name = 'python-eval'
    def process(self, connection, source, target, args):
        expr = u' '.join(args)
        
        try:
            result = unicode(evaluator(expr))
            msg = result[:100]
            if result != msg:
                msg += '...'
            
            return {'action': self.Action.PRIVMSG,
                    'target': target,
                    'message': (msg,)
                    }
        except SyntaxError:
            return {'action': self.Action.PRIVMSG,
                    'target': target,
                    'message': (u'Syntax Error',)
                    }
        except Exception, e:
            ename = e.__class__.__name__
            msg = '%s: %s' % (ename, e)
            return {'action': self.Action.PRIVMSG,
                    'target': target,
                    'message': (msg,)
                    }
            

