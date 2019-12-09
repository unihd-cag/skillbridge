from os.path import abspath, dirname, join
from argparse import ArgumentParser

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
    parser = ArgumentParser('skillbridge', description="""
        Without arguments, prints the location of the skill script.
        The correct location is required for the load command.
        """)
    parser.add_argument('-g', '--generate', help="generate static completion file",
                        action='store_true', default=False)
    args = parser.parse_args()

    if args.generate:
        generate_static_completion()
    else:
        print_skill_script_location()


if __name__ == '__main__':
    main()
