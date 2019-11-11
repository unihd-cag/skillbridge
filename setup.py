from setuptools import setup, find_packages, Command
from re import match

import skillbridge


def comparable_version(version):
    return tuple(int(i) for i in version.split('.'))


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

        highest_tag = max(comparable_version(tag.tag.tag.split('/')[-1]) for tag in repo.tags)
        version = skillbridge.__version__

        if repo.is_dirty():
            print(f"You must commit all changes before you can create a tag!")
            return

        print(f"Current version is {version!r}")
        one_higher = comparable_version(version)
        one_higher = *one_higher[:2], one_higher[2] + 1
        one_higher = '.'.join(str(i) for i in one_higher)
        new_version = input(f"Enter the new version ({one_higher}): ") or one_higher

        if not match(r'\d+\.\d+\.\d+', new_version):
            print("Version must be of this format: NUMBER.NUMBER.NUMBER")
            return

        if comparable_version(new_version) <= comparable_version(version):
            print("The new version must be higher than the current version")
            return

        if comparable_version(new_version) <= highest_tag:
            print("The new version must be higher than the tagged version")
            return

        with open('skillbridge/__init__.py') as fin:
            code = fin.readlines()

        with open('skillbridge/__init__.py', 'w') as fout:
            for line in code:
                if line.startswith('__version__'):
                    fout.write(f"__version__ = {new_version!r}\n")
                else:
                    fout.write(line)
        repo.index.add(['skillbridge/__init__.py'])
        repo.index.commit(f"bump version {new_version!r}")
        print(f"Changes committed as {repo.active_branch.commit.message!r}")
        print("Use `git push` to upload the commit")
        tag = repo.create_tag(f'releases/{new_version}',
                              message=f'release {new_version}').tag
        print(f"Tag created as {tag.tag!r} with message {tag.message!r}")
        print("Use `git push --tags` to upload the tag")


with open('README.md') as fin:
    long_description = fin.read()

with open('dev-requirements.txt') as fin:
    dev_requirements = fin.read().split()


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
    package_data={'skillbridge': ['py.typed']},
    include_package_data=True,
    extras_require={
        'dev': dev_requirements
    },
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
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    ]
)

if __name__ == '__main__':
    setup(**config)
