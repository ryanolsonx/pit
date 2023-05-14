#!/usr/bin/env python3

from setuptools import setup

setup(name = 'pit',
      version = '0.1.0',
      packages = ['pit'],
      entry_points = {
          'console_scripts': [
              'pit = pit.cli:main'
          ]
      })
