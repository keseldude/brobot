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
import shelve
import logging

log = logging.getLogger(__name__)

DEFINED = []
SHELF_KEY = 'defined_plugins'

class DefinePlugin(bot.CommandPlugin):
    name = 'define'
    def load(self):
        plugins = []
        shelf = shelve.open(self.shelf_path)
        try:
            if shelf.has_key(SHELF_KEY):
                plugins = shelf[SHELF_KEY]
        finally:
            shelf.close()
        
        for f_name, expr in plugins:
            plugin = self.create_plugin(f_name, expr)
            if plugin:
                self.ircbot.register_command_plugin(plugin.name, plugin)
                DEFINED.append((f_name, expr))
    
    def process(self, connection, source, target, args):
        if len(args) < 2:
            return None
        
        f_name = args[0]
        expr = u' '.join(args[1:])
        if 'lambda' not in expr:
            return self.privmsg(target, 'Needs lambda')
        plugin = self.create_plugin(f_name, expr, target)
        if isinstance(plugin, dict):
            return plugin
        
        if not self.ircbot.register_command_plugin(plugin.name, plugin):
            return self.privmsg(target, 'Command already defined. Sorry.')
        shelf = shelve.open(self.shelf_path)
        try:
            if shelf.has_key(SHELF_KEY):
                plugins = shelf[SHELF_KEY]
            else:
                plugins = []
            
            plugins.append((f_name, expr))
            shelf[SHELF_KEY] = plugins
        finally:
            shelf.close()
        
        DEFINED.append((f_name, expr))
        return self.privmsg(target, u'Defined %s.' % f_name)
    
    def create_plugin(self, f_name, expr, target=None):
        try:
            lmbda = evaluator(expr)
        except SyntaxError:
            if target is None:
                return False
            return self.privmsg(target, 'Syntax Error')
        if target is not None:
            if len(inspect.getargspec(lmbda)[0]) != 1:
                return self.privmsg(target, 'Lambda must have one argument')
        class DefinedPlugin(bot.CommandPlugin):
            name = f_name
            def process(self, c, s, t, a):
                try:
                    result = lmbda(u' '.join(a))
                except Exception as e:
                    ename = e.__class__.__name__
                    msg = '%s: %s' % (ename, e)
                    return self.privmsg(t, msg)
                else:
                    return self.privmsg(t, result)
        return DefinedPlugin

class UndefinePlugin(bot.CommandPlugin):
    name = 'undefine'
    def process(self, connection, source, target, args):
        f_name = u' '.join(args)
        f_expr = None
        for name, expr in DEFINED:
            if name == f_name:
                f_expr = expr
                break
        if f_expr is not None:
            if not self.ircbot.unregister_command_plugin(f_name):
                return self.privmsg(target, u'Could not remove plugin %s.' % f_name)
            f_pair = (f_name, f_expr)
            DEFINED.remove(f_pair)
            shelf = shelve.open(self.shelf_path)
            try:
                if shelf.has_key(SHELF_KEY):
                    plugins = shelf[SHELF_KEY]
                    plugins.remove(f_pair)
                    shelf[SHELF_KEY] = plugins
            except ValueError:
                log.error('Unable to remove the plugin... something is wrong.')
            finally:
                shelf.close()
            return self.privmsg(target, u'Undefined %s.' % f_name)
        else:
            return self.privmsg(target, u'No such plugin has been defined.')
    

