from pathlib import Path
from sys import argv
from subprocess import check_output, check_call


def find_hash(ref: str) -> str:
    return check_output(['git', 'rev-parse', ref]).decode().strip()


def check_up_to_date(ref: str) -> None:
    master_hash = find_hash('master')
    release_hash = find_hash(ref)

    if master_hash != release_hash:
        print("Master and current release are different commits, cannot release")
        exit(1)


def checkout_master() -> None:
    check_call(['git', 'checkout', 'master'])


def bump_version(ref: str) -> None:
    *_, version = ref.split('/')
    here = Path(__file__).parent
    version_py = here / 'skillbridge' / 'version.py'

    version_py.write_text(f"__version__ = '{version}'\n")


if __name__ == '__main__':
    _, release_ref = argv

    check_up_to_date(release_ref)
    checkout_master()
    bump_version(release_ref)
