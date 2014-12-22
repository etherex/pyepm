from setuptools import setup, find_packages
import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'pyepm/_version.py'
versioneer.versionfile_build = 'pyepm/_version.py'
versioneer.tag_prefix = '' # tags are like 1.2.0
versioneer.parentdir_prefix = 'pyepm-' # dirname like 'myproject-1.2.0'

console_scripts = ['pyepm=pyepm.pyepm:main']

setup(name="pyepm",
      packages=find_packages("."),
      description='Python Ethereum Package Manager',
      url='https://github.com/etherex/pyepm/',
      install_requires=[
          'pyethereum',
          'ethereum-serpent',
          'requests'
      ],
      entry_points=dict(console_scripts=console_scripts),
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass())
