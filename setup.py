import sys
from os.path import join, dirname, abspath

from setuptools import setup, find_packages

# this is a trick to get the version before the package is installed
directory = dirname(abspath(__file__))
sys.path.insert(0, join(directory, 'bigg_models'))
version = __import__('version').__version__

setup(
    name='BiGG Models',
    version=version,
    author='Justin Lu & Zachary King',
    author_email='zaking@ucsd.edu',
    url='http://bigg.ucsd.edu',
    packages=find_packages(),
    package_data={'bigg_models': ['static/assets/*', 'static/css/*',
                                  'static/js/*', 'static/lib/*',
                                  'static/lib/tablesorter/*',
                                  'templates/*']},
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        'cobradb>=0.3.0,<0.4',
        'Jinja2>=2.10.3,<3',
        'simplejson>=3.16.0,<4',
        'progressbar2>=3.47.0,<4',
    ],
)
