# -*- coding: utf-8 -*-
# Author: Matías Bordese

import codecs
import os

from setuptools import find_packages, setup


# metadata
NAME = 'unidiff'
DESCRIPTION = 'Unified diff parsing/metadata extraction library.'
KEYWORDS = ['unified', 'diff', 'parse', 'metadata']
URL = 'http://github.com/matiasb/python-unidiff'
EMAIL = 'mbordese@gmail.com'
AUTHOR = 'Matias Bordese'
LICENSE = 'MIT'

HERE = os.path.abspath(os.path.dirname(__file__))

# use README as the long-description
with codecs.open(os.path.join(HERE, 'README.rst'), "rb", "utf-8") as f:
    long_description = f.read()


# load __version__.py module as a dictionary
about = {}
with open(os.path.join(HERE, 'unidiff/__version__.py')) as f:
    exec(f.read(), about)


setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    keywords=KEYWORDS,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    scripts=['bin/unidiff'],
    include_package_data=True,
    license=LICENSE,
    classifiers=[
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    test_suite='tests',
)
