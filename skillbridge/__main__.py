from os.path import abspath, dirname, join
from argparse import ArgumentParser
from pathlib import Path
from shutil import copy
from typing import Dict, Tuple, Any, Callable, Optional

from . import generate_static_completion
from .client.extract import functions_by_prefix


def print_skill_script_location() -> None:
    folder = dirname(abspath(__file__))
    skill_source = join(folder, 'server', 'python_server.il')
    escaped = repr(skill_source)[1:-1]

    print("Path to Skill server script:")
    print(escaped)

    print()

    print("Type this into the Skill console:")
    print(f'load("{escaped}")')


def show_status() -> None:
    prefixes = functions_by_prefix()
    function_count = sum(len(collection) for collection in prefixes.values())

    if prefixes:
        print(f"There are {function_count} functions in {len(prefixes)} prefixes")
    else:
        print("No function definitions are exported")


def export_definitions(path: Path) -> None:
    if path.is_dir():
        path /= 'definitions.txt'

    if path.exists():
        if input("{} already exists, overwrite? [yN]").lower() != 'y':
            exit()

    definitions = Path(__file__).parent / 'client' / 'definitions.txt'

    copy(definitions, path)
    print("copied")


def import_definitions(path: Path, always_overwrite: bool) -> None:
    if path.is_dir():
        path /= 'definitions.txt'

    definitions = Path(__file__).parent / 'client' / 'definitions.txt'

    if definitions.exists() and not always_overwrite:
        try:
            if input("definitions already exist, overwrite? [yN]").lower() != 'y':
                exit()
        except KeyboardInterrupt:
            exit()

    copy(path, definitions)
    show_status()


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
    status = sub.add_parser('status', help="show the number of exported function definitions")
    export = sub.add_parser('export', help="export the function definitions into a text file")
    export.add_argument('path', help="The absolute path for the exported file", type=Path)
    imp = sub.add_parser('import', help="import the function definitions from a file")
    imp.add_argument('path', help="The absolute path for the exported file", type=Path)
    imp.add_argument('-f', '-force', '--force', help="always overwrite", action='store_true')
    args = parser.parse_args()

    commands: Dict[Optional[str], Tuple[Any, Callable[[], None]]] = {
        None: (parser, parser.print_help),
        'status': (status, show_status),
        'path': (path, print_skill_script_location),
        'generate': (generate, generate_static_completion),
        'export': (export, lambda: export_definitions(args.path)),
        'import': (imp, lambda: import_definitions(args.path, args.force)),
    }

    sub_parser, func = commands[args.command]
    try:
        func()
    except RuntimeError as e:
        sub_parser.error(str(e))


if __name__ == '__main__':
    main()
