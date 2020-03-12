from setuptools import setup, find_packages

with open('skillbridge/version.py') as fin:
    data = {}
    exec(fin.read(), data)
    version = data['__version__']

with open('README.md') as fin:
    long_description = fin.read()

with open('dev-requirements.txt') as fin:
    dev_requirements = fin.read().split()


config = dict(
    name="skillbridge",
    version=version,
    author="Niels Buwen",
    author_email="dev@niels-buwen.de",
    description="A seamless Python remote bridge to Cadence's Skill in Virtuoso",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/unihd-cag/skillbridge",
    packages=find_packages(),
    package_data={'skillbridge': ['py.typed']},
    include_package_data=True,
    extras_require={'dev': dev_requirements},
    entry_points={'console_scripts': ['skillbridge = skillbridge.__main__:main']},
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
    ],
)

if __name__ == '__main__':
    setup(**config)
