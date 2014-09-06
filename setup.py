# -*- coding: utf-8 -*-
# Author: Matías Bordese

from setuptools import setup, find_packages

from unidiff import VERSION

setup(
    name='unidiff',
    version=VERSION,
    description="Unified diff parsing library.",
    keywords='unified diff parse',
    author='Matias Bordese',
    author_email='mbordese@gmail.com',
    url='http://github.com/matiasb/python-unidiff',
    license='MIT',
    packages=find_packages(),
    scripts=['bin/unidiff'],
)
