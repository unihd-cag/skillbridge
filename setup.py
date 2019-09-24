from setuptools import setup, find_packages, Extension
from distutils.command.build_ext import build_ext
from traceback import print_exc


class BuildFailed(Exception):
    pass


class OptionalExtension(build_ext):
    def run(self):
        try:
            super().run()
        except Exception:
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            super().build_extension(ext)
        except Exception:
            raise BuildFailed()


with open('README.md') as fin:
    long_description = fin.read()

with open('dev-requirements.txt') as fin:
    dev_requirements = fin.read().split()

fast_parser = Extension(
    'skillbridge.cparser.parser',
    define_macros=[
        ('YYERROR_VERBOSE', 1)
    ],
    sources=[
        'skillbridge/cparser/parser.c',
        'skillbridge/cparser/generated/lexer.c',
        'skillbridge/cparser/generated/parser.c'
    ],
    extra_compile_args='-std=c11 -Wall -Wextra -Wpedantic'.split(),
    language='c'
)

config = dict(
    name="skillbridge",
    version="0.1.0",
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
    ext_modules=[fast_parser],
    cmdclass=dict(build_ext=OptionalExtension),
    classifiers=[
        "Development Status :: Alpha",
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
    try:
        setup(**config)
    except BuildFailed:
        print("*******************************************************")
        print("* Something went wrong while building the C extension *")
        print("*******************************************************")

        print_exc()

        print("***********************************")
        print("* Building the C extension failed *")
        print("* Retrying without C extension    *")
        print("* Speedups will not be enabled    *")
        print("***********************************")

        config.pop('ext_modules')
        config.pop('cmdclass')

        setup(**config)
