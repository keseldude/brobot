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