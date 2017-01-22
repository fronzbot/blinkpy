# -*- coding: utf-8 -*-

from blinkpy import __version__
from setuptools import setup

setup(
    name = 'blinkpy',
    version = __version__,
    description = 'A Blink camera Python library',
    long_description='A library that communicates with Blink cameras',
    author = 'Kevin Fronczak',
    author_email = "kfronczak@gmail.com",
    license='MIT',
    url = 'https://github.com/fronzbot/blinkpy',
    py_modules=['blinkpy'],
    install_requires=['requests'],
    classifiers=[
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: MIT License',
      'Programming Language :: Python :: 3.4',
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6',
      'Environment :: Plugins',
      'Environment :: Web Environment'
      ]
)