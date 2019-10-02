from setuptools import setup, find_packages, Extension, Command
import skillbridge


class TagVersion(Command):
    """
    Tag the latest commit using the version information form the package
    """

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @staticmethod
    def run():
        from git import Repo

        repo = Repo('.')

        branch = repo.active_branch.name
        if branch != 'master':
            print(f"Can only tag on master. You are on branch {branch!r}!")
            return

        tags = {tag.name for tag in repo.tags}
        version = skillbridge.__version__
        if any(version in tag for tag in tags):
            print(f"Version {version!r} was already tagged!")
            return

        if repo.is_dirty():
            print(f"You must commit all changes before you can create a tag!")
            return

        tag = repo.create_tag(f'releases/{version}', message=f'release {version}').tag
        print(f"Tag created as {tag.tag!r} with message {tag.message!r}")
        print("Use `git push --tags` to upload the tags")


with open('README.md') as fin:
    long_description = fin.read()

with open('dev-requirements.txt') as fin:
    dev_requirements = fin.read().split()

parser = Extension(
    'skillbridge.parser.cparser',
    define_macros=[
        ('YYERROR_VERBOSE', 1)
    ],
    sources=[
        'skillbridge/parser/cparser.c',
        'skillbridge/parser/generated/lexer.c',
        'skillbridge/parser/generated/parser.c'
    ],
    extra_compile_args='-std=c11 -Wall -Wextra -Wpedantic'.split(),
    language='c'
)


config = dict(
    name="skillbridge",
    version=skillbridge.__version__,
    author="Niels Buwen",
    author_email="dev@niels-buwen.de",
    description="A seamless Python remote bridge to Cadence's Skill in Virtuoso",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/unihd-cag/skillbridge",
    packages=find_packages(),
    include_package_data=True,
    extras_require={
        'dev': dev_requirements
    },
    ext_modules=[parser],
    cmdclass={
        'tag': TagVersion,
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: Software Development",
        "License :: OSI Approved :: MIT License",
    ]
)

if __name__ == '__main__':
    setup(**config)
