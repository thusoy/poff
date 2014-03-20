#!/usr/bin/env python
from setuptools import setup

install_requires = [
    'flask',
    'flask-sqlalchemy',
    'flask-wtf',
    'wtforms-alchemy',
]

setup(
    name='poff',
    version='0.1.0',
    author='Tarjei Husøy',
    author_email='tarjei@roms.no',
    url='https://github.com/thusoy/poff',
    description="A quite small pdns frontend",
    py_modules=['poff'],
    install_requires=install_requires,
    extras_require={
        'test': ['nose', 'coverage'],
        'postgres': ['psycopg2'],
    },
    entry_points={
        'console_scripts': [
            'poff = poff:serve',
        ]
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
