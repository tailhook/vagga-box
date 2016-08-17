#!/usr/bin/env python3

from setuptools import setup

setup(name='vagga-box',
      version='0.1',
      description='A wrapper to run vagga in virtualbox (easier on osx)',
      author='Paul Colomiets',
      author_email='paul@colomiets.name',
      url='http://github.com/tailhook/vagga-box',
      packages=['vagga_box'],
      install_requires=[
        'PyYaml',
        'macfsevents',
      ],
      entry_points = {
          'console_scripts': [
              'vagga=vagga_box.main:main',
              'unison-fsevents=unox:main',
          ],
      },
      classifiers=[
          'Development Status :: 4 - Beta',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
      ],
      )
