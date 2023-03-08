from pathlib import Path
from sys import argv

_, ref = argv
*_, version = ref.split('/')
here = Path(__file__).parent
version_py = here / 'skillbridge' / 'version.py'

version_py.write_text(f"__version__ = '{version}'\n")
