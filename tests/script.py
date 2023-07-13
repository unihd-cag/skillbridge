from sys import argv
from time import sleep
from ast import literal_eval

from skillbridge import Workspace, Symbol


ws = Workspace.open(direct=True)

_, variable_name, value, delay = argv

sleep(float(delay))

ws['set'](Symbol(variable_name),  literal_eval(value))
