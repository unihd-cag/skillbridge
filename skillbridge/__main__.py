from os.path import abspath, dirname, join
from argparse import ArgumentParser
from typing import Dict, Tuple, Any, Callable, Optional

from . import generate_static_completion


def print_skill_script_location() -> None:
    folder = dirname(abspath(__file__))
    skill_source = join(folder, 'server', 'python_server.il')
    escaped = repr(skill_source)[1:-1]

    print("Path to Skill server script:")
    print(escaped)

    print()

    print("Type this into the Skill console:")
    print(f'load("{escaped}")')


def main() -> None:
    parser = ArgumentParser(
        'skillbridge',
        description="""
        CLI utility for the various skillbridge management commands
        """,
    )

    sub = parser.add_subparsers(title='commands', dest='command')

    path = sub.add_parser('path', help="show the path to the skill script")
    generate = sub.add_parser('generate', help="generate static completion file")
    args = parser.parse_args()

    commands: Dict[Optional[str], Tuple[Any, Callable[[], None]]] = {
        None: (parser, parser.print_help),
        'path': (path, print_skill_script_location),
        'generate': (generate, generate_static_completion),
    }

    sub_parser, func = commands[args.command]
    try:
        func()
    except RuntimeError as e:
        sub_parser.error(str(e))


if __name__ == '__main__':
    main()
