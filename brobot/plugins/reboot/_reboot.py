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

import sys
import os
import signal
from subprocess import Popen
import ctypes

def kill(pid, signal):
    if sys.platform == 'win32':
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(1, 0, pid)
        kernel32.TerminateProcess(handle, 0)
    else:
        os.kill(pid, signal)

def main(args):
    pid = None
    with open(args[0], 'r') as pidfile:
        pid = int(pidfile.read())
    
    if pid is not None:
        kill(pid, signal.SIGTERM)
        Popen([args[1], args[2]])
    

if __name__ == '__main__':
    main(sys.argv[1:])