from typing import Tuple

from sys import stderr, exit
from subprocess import check_call, check_output


def to_comparable(version: str) -> Tuple[int, ...]:
    return tuple(int(i) for i in version.split('.'))


def assert_version(tool: str, required: str) -> None:
    version = check_output([tool, '--version']).splitlines()[0].split()[-1].decode()
    print(tool, "version is", version)
    print("required is", required)

    if to_comparable(version) < to_comparable(required):
        print("exiting")
        exit(1)
    else:
        print("ok")


if __name__ == '__main__':
    assert_version('flex', '2.6.0')
    assert_version('bison', '3.0.0')

    try:
        check_call(['flex', 'skill.l'])
    except FileNotFoundError:
        print("You must install 'flex' first", file=stderr)
        exit(1)

    try:
        check_call(['bison', 'skill.y'])
    except FileNotFoundError:
        print("You must install 'bison' first", file=stderr)
        exit(2)
