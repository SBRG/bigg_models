# -*- coding: utf-8 -*-

import sys
from os.path import join, dirname, abspath

from setuptools import setup, Command

# this is a trick to get the version before the package is installed
directory = dirname(abspath(__file__))
sys.path.insert(0, join(directory, 'bigg_models'))
version = __import__('version').__version__

setup(name='BiGG Models',
      version=version,
      author='Justin Lu & Zachary King',
      url='http://bigg.ucsd.edu',
      packages=['bigg_models'],
      package_data={'bigg_models': ['static/assets/*', 'static/css/*',
                                    'static/js/*', 'static/lib/*',
                                    'static/lib/tablesorter/*',
                                    'templates/*']},
      install_requires=['Jinja2>=2.7.3',
                        'tornado>=4.0.2',
                        'pytest>=2.6.4',
                        'ome>=0.1.0',
                        'python-libsbml>=5.12.1'])
