import string
import random
from datetime import datetime, date, timedelta
import itertools
import operator
import struct
import re
import math
import decimal

__all__ = ['evaluator']

def forbidden(*args, **kwargs):
    return 'No (forbidden content)'

FORBIDDEN_FUNCTIONS = ('__import__',
                       'open',
                       'file',
                       'exit',
                       'quit',
                       'compile',
                       'input',
                       'execfile',
                       'exec',
                       'reload',
                       'raw_input',
                       'print',
                       'memoryview')

gs = { 'string': string,
       'random': random,
       'datetime': datetime,
       'date': date,
       'timedelta': timedelta,
       'itertools': itertools,
       'operator': operator,
       'struct': struct,
       're': re}
        
for x in dir(math):
    if not x.startswith('__'):
        gs[x] = getattr(math, x)

for x in dir(decimal):
    if not x.startswith('__'):
        gs[x] = getattr(decimal, x)

for func in FORBIDDEN_FUNCTIONS:
    gs[func] = forbidden

def evaluator(expr):
    return eval(expr, gs, {})