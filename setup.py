#!/usr/bin/env python

from setuptools import setup, find_packages

requires = ['diff-match-patch']

setup(name='revisor',
      version='0.1',
      description='Tool for serializing revisioned text type data for use in databases',
      author='Isaac Cook',
      author_email='isaac@simpload.com',
      install_requires=requires,
      packages=find_packages()
      )
