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
import inspect

DEFINED = []

class DefinePlugin(bot.CommandPlugin):
    name = 'define'
    def process(self, connection, source, target, args):
        if len(args) < 2:
            return None
        
        f_name = args[0]
        expr = u' '.join(args[1:])
        if 'lambda' not in expr:
            return None
        try:
            lmbda = evaluator(expr)
        except SyntaxError:
            return {'action': self.Action.PRIVMSG,
                    'target': target,
                    'message': (u'Syntax Error',)
                    }
        
        if len(inspect.getargspec(lmbda)[0]) != 1:
            return None
        
        class DefinedPlugin(bot.CommandPlugin):
            name = f_name
            def process(self, c, s, t, a):
                try:
                    result = lmbda(u' '.join(a))
                except Exception, e:
                    ename = e.__class__.__name__
                    msg = '%s: %s' % (ename, e)
                    return {'action': self.Action.PRIVMSG,
                            'target': target,
                            'message': (msg,)
                            }
                else:
                    return {'action': self.Action.PRIVMSG,
                            'target': target,
                            'message': (result,)
                            }
        
        if not self.ircbot.register_command_plugin(f_name, DefinedPlugin):
            return {'action': self.Action.PRIVMSG,
                    'target': target,
                    'message': (u'Command already defined. Sorry.',)
                    }
        
        DEFINED.append(f_name)
        
        return {'action': self.Action.PRIVMSG,
                'target': target,
                'message': (u'Defined %s.' % f_name,)
                }
    

class UndefinePlugin(bot.CommandPlugin):
    name = 'undefine'
    def process(self, connection, source, target, args):
        f_name = u' '.join(args)
        if f_name in DEFINED:
            if not self.ircbot.unregister_command_plugin(f_name):
                return {'action': self.Action.PRIVMSG,
                        'target': target,
                        'message': (u'Could not remove plugin %s.' % f_name,)
                        }
            DEFINED.remove(f_name)
            return {'action': self.Action.PRIVMSG,
                    'target': target,
                    'message': (u'Undefined %s.' % f_name,)
                    }
        else:
            return {'action': self.Action.PRIVMSG,
                    'target': target,
                    'message': (u'No such plugin has been defined.',)
                    }
    

