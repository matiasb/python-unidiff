# -*- coding: utf-8 -*-
# Author: Matías Bordese

from __future__ import unicode_literals

from setuptools import setup, find_packages

from unidiff import VERSION

setup(
    name='unidiff',
    version=VERSION,
    description="Unified diff parsing/metadata extraction library.",
    keywords='unified diff parse metadata',
    author='Matias Bordese',
    author_email='mbordese@gmail.com',
    url='http://github.com/matiasb/python-unidiff',
    license='MIT',
    packages=find_packages(),
    scripts=['bin/unidiff'],
    classifiers=[
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
)
