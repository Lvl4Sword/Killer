#!/usr/bin/env python3

from pathlib import Path

from setuptools import find_packages, setup

from killer import __author__, __license__, __version__


setup(
    name='killer',
    version=__version__,
    author=__author__,
    # author_email='',
    description='Shuts the system down upon disallowed changes',
    # This is what you see on PyPI page
    long_description=Path('README.md').read_text(encoding='utf-8'),
    # PEP 566, PyPI Warehouse, setuptools>=38.6.0 make markdown possible
    long_description_content_type='text/markdown',
    url='https://github.com/Lvl4Sword/Killer',
    project_urls={
        'Discord Server': 'https://discord.gg/bTRxxMJ',
        'IRC': 'https://webchat.freenode.net/?channels=%23killer',
    },
    license=__license__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    # These enable commandline usage of the tool
    entry_points={
        'console_scripts': [
            'killer = killer.killer:main'
        ]
    },
    install_requires=Path('requirements.txt').read_text(encoding='utf-8').split(),
    tests_require=[
        'coverage',
        'pytest',
        'pytest-cov',
    ],
    python_requires='>=3.5',
    platforms=['Linux', 'Windows'],
    keywords=[
        'killer', 'kill', 'watch', 'watchdog', 'monitoring', 'monitor',
        'tamper', 'tampering', 'tamper-evident', 'shutdown', 'poweroff',
    ],
    classifiers=[
        # Used by PyPI to classify the project and make it browsable
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU Affero General Public License v3',

        'Operating System :: Microsoft :: Windows',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: Microsoft :: Windows :: Windows 8.1',
        'Operating System :: Microsoft :: Windows :: Windows 8',
        'Operating System :: Microsoft :: Windows :: Windows 7',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',

        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',

        'Topic :: System :: Systems Administration',
        'Topic :: System :: Networking :: Monitoring :: Hardware Watchdog',
        'Topic :: System :: Monitoring',
        'Topic :: System',
        'Topic :: Utilities',
    ]
)
