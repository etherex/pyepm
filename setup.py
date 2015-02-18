#!/usr/bin/env python

from setuptools import setup, find_packages
import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'pyepm/_version.py'
versioneer.versionfile_build = 'pyepm/_version.py'
versioneer.tag_prefix = ''  # tags are like 1.2.0
versioneer.parentdir_prefix = 'pyepm-'  # dirname like 'myproject-1.2.0'

CONSOLE_SCRIPTS = ['pyepm=pyepm.pyepm:main']
LONG = """
Python-based EPM (Ethereum Package Manager) for Serpent 2 contract deployment using YAML for package definitions.
"""

setup(name="pyepm",
      packages=find_packages("."),
      description='Python Ethereum Package Manager',
      long_description=LONG,
      author="caktux",
      author_email="caktux@gmail.com",
      url='https://github.com/etherex/pyepm/',
      install_requires=[
          'pyyaml',
          'pyethereum',
          'ethereum-serpent',
          'requests'
      ],
      entry_points=dict(console_scripts=CONSOLE_SCRIPTS),
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      classifiers=[
          "Development Status :: 2 - Pre-Alpha",
          "Environment :: Console",
          "License :: OSI Approved :: MIT License",
          "Operating System :: MacOS :: MacOS X",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python :: 2.7",
      ])
