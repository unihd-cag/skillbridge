from __future__ import annotations

from argparse import ArgumentParser
from code import interact
from pathlib import Path
from random import randrange
from typing import Any, Callable

from . import generate_static_completion

here = Path(__file__).parent.resolve()


def print_skill_script_location() -> None:
    skill_source = here / 'server' / 'python_server.il'

    print("Path to Skill server script:")
    print(skill_source)

    print()

    print("Type this into the Skill console:")
    print(f'load("{skill_source}")')


def deprecated_command() -> None:  # pragma: no cover
    print("This command is deprecated")
    print("It is no longer necessary to export function definitions")
    print("You don't have to do anything")


def shell_command(ws_id: str | None, ping: bool) -> None:
    import skillbridge

    variables = {name: getattr(skillbridge, name) for name in dir(skillbridge)}
    ws = skillbridge.Workspace.open(ws_id)
    variables['ws'] = ws

    if ping:
        x = randrange(1000)
        y = randrange(1000)

        assert ws['plus'](x, y) == x + y, "simple command failed"

    interact("Interactive Python interpreter with skillbridge Workspace `ws`", local=variables)


def main() -> None:
    parser = ArgumentParser(
        'skillbridge',
        description="""
        CLI utility for the various skillbridge management commands
        """,
    )

    sub = parser.add_subparsers(title='commands', dest='command')

    shell = sub.add_parser('shell', help="opens a python interpreter with a connected workspace")
    shell.add_argument('-i', '--id', help="id used to open the workspace", default=None)
    shell.add_argument(
        '-p',
        '--ping',
        help="ping the server and quit if it does not respond",
        action='store_true',
    )
    path = sub.add_parser('path', help="show the path to the skill script")
    generate = sub.add_parser('generate', help="generate static completion file")
    status = sub.add_parser('status', help="deprecated, not needed anymore")
    export = sub.add_parser('export', help="deprecated, not needed anymore")
    export.add_argument('path', help="deprecated", type=str)
    imp = sub.add_parser('import', help="deprecated, not needed anymore")
    imp.add_argument('path', help="deprecated", type=str)
    imp.add_argument('-f', '-force', '--force', help="deprecated", action='store_true')
    args = parser.parse_args()

    commands: dict[str | None, tuple[Any, Callable[[], None]]] = {
        None: (parser, parser.print_help),
        'status': (status, deprecated_command),
        'path': (path, print_skill_script_location),
        'generate': (generate, generate_static_completion),
        'export': (export, deprecated_command),
        'import': (imp, deprecated_command),
        'shell': (shell, lambda: shell_command(args.id, args.ping)),
    }

    sub_parser, func = commands[args.command]
    try:
        func()
    except RuntimeError as e:  # pragma: no cover
        sub_parser.error(str(e))


if __name__ == '__main__':  # pragma: no cover
    main()
