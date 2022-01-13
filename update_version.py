from pathlib import Path
from sys import argv

_, ref = argv
*_, version = ref.split('/')
here = Path(__file__).parent
setup_cfg = here / 'setup.cfg'
version_py = here / 'skillbridge' / 'version.py'

setup_cfg.write_text(setup_cfg.read_text().replace('version = dev', f'version = {version}'))
version_py.write_text(f"__version__ = '{version}'\n")
