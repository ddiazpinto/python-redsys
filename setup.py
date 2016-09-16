#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

VERSION = '0.1.0'
PACKAGES = ['redsys', ]

setup(
    name='redsys',
    description='A simple client to handle payments through RedSys.',
    keywords="redsys, payment, sermepa",
    author='David Díaz',
    author_email='d.diazp@gmail.com',
    url='https://github.com/ddiazpinto/python-redsys',
    version=VERSION,
    license='MIT',
    provides=['redsys'],
    install_requires=[],
    packages=PACKAGES,
    scripts=[],
)
