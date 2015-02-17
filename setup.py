#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup, find_packages
import sys

install_requires = [
    'flask',
    'flask-sqlalchemy',
    'flask-wtf',
    'pyyaml',
    'wtforms-alchemy',
]

if sys.version_info < (2, 7, 0):
    install_requires.append('argparse')

setup(
    name='poff',
    version='1.1.1',
    author='Tarjei Husøy',
    author_email='tarjei@roms.no',
    url='https://github.com/thusoy/poff',
    description="A quite small pdns frontend",
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={
        'test': ['nose', 'coverage', 'tox'],
        'postgres': ['psycopg2'],
    },
    entry_points={
        'console_scripts': [
            'poff = poff.cli:cli_entry',
        ]
    },
    package_data={
        '': [
            'templates/*.html',
            'static/*.css',
        ],
    },
    classifiers=[
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Web Environment',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        # 'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
)
