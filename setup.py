"""
DEPRECATED.
this file only exists to make `pip install -e` work for now

A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# get __version__ from _version.py
from bat._version import __version__

# Get the long description from the relevant file
long_description = '''
Deprecated install method.
this file only exists to make `pip install -e` work for now
'''

with open('requirements.txt') as f:
    requirements = f.read().splitlines()


setup(
    # Application name:
    name="BAT",

    # Version number (initial):
    version=__version__,

    # Application author details:
    author="lundy bernard",
    author_email="lundy.bernard@gmail.com",

    license='MIT',

    # Packages
    packages=find_packages(),
    package_data={'': ['*.yaml'], },
    include_package_data=True,
    zip_safe=False,

    # entry points, to generate executables in python/bin/
    entry_points={
        "console_scripts":
            ['bat = bat.cli:BATCLI']
    },

    description="Developer Install Method",

    long_description=long_description,

    # Dependent packages (distributions)
    install_requires=requirements,
)
