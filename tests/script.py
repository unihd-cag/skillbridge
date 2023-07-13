from ast import literal_eval
from sys import argv
from time import sleep

from skillbridge import Symbol, Workspace

ws = Workspace.open(direct=True)

_, variable_name, value, delay = argv

sleep(float(delay))

ws['set'](Symbol(variable_name), literal_eval(value))
