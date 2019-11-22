# Author: Alejandro M. BERNARDIS
# Email: alejandro.bernardis@gmail.com
# Created: 2019/11/22 14:13
# ~

from os import path
from io import open
from setuptools import setup, find_packages
from aysa.docker.registry import __version__ as registry

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'readme.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=registry.__title__,
    version=registry.__version__,
    description=registry.__summary__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=registry.__uri__,
    author=registry.__author__,
    author_email=registry.__email__,
    keywords='docker registry services development deployment',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    python_requires='>=3.6.*, <4',

    package_data={
        '': ['LICENSE', 'README.md']
    },

    install_requires=[
        'requests==2.22.0'
    ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],

    entry_points={
        'console_scripts': [
            # 'aysar=registry.cli:main',
        ],
    },

    project_urls={
        'Bug Reports': registry.__issues__,
        'Source': registry.__uri__,
    },

)
