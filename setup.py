# -*- coding: utf-8 -*-

import sys
from os.path import join, dirname, realpath

try:
    from setuptools import setup, Command
except:
    from distutils.core import setup, Command

# this is a trick to get the version before the package is installed
directory = dirname(realpath(__file__))
sys.path.insert(0, join(directory, 'bigg2'))
version = __import__('version').__version__

setup(name='BiGG 2',
      version=version,
      author='Justin Lu',
      url='http://bigg.ucsd.edu',
      packages=['bigg2'],
      package_data={'bigg2': ['static/assets/*', 'static/css/*',
                             'static/js/*', 'static/lib/*',
                             'static/lib/tablesorter/*',
                             'templates/*']},
      install_requires=['Jinja2>=2.7.3',
                        'tornado>=4.0.2',
                        'pytest>=2.6.2',
                        'python-libsbml>=5.11.0', # may require sudo
                        'ome==0.0.1-bigg'])
