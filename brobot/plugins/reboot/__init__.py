from core import bot
from subprocess import Popen
from threading import Thread
import os.path

class RebootPlugin(bot.CommandPlugin):
    name = 'reboot'
    admin = True
    reboot_script_path = \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '_reboot.py')
    def load(self):
        self.python_binary = self.ircbot.settings['python_binary']
        self.brobot_path = \
                        os.path.expanduser(self.ircbot.settings['brobot_path'])
    
    def reboot(self):
        self.ircbot.exit()
        Popen([self.python_binary, self.reboot_script_path,
                   self.ircbot.pid_path, self.python_binary, self.brobot_path])
    
    def process(self, connection, source, target, args):
        if self.ircbot.is_admin(connection.server, source.nick):
            t = Thread(target=self.reboot)
            t.daemon = False
            t.start()
    
