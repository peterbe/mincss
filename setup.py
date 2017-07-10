#!/usr/bin/env python

import io
import os
import re


# Prevent spurious errors during `python setup.py test`, a la
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html:
try:
    import multiprocessing
    multiprocessing = multiprocessing  # shut up pyflakes
except ImportError:
    pass

from setuptools import setup, find_packages


def read(*parts):
    with io.open(os.path.join(os.path.dirname(__file__), *parts)) as f:
        return f.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        version_file,
        re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


def find_install_requires():
    return [
        x.strip() for x in
        read('requirements.txt').splitlines()
        if x.strip() and not x.startswith('#')
    ]


setup(
    name='mincss',
    version=find_version('mincss/__init__.py'),
    description='clears the junk out of your CSS',
    long_description=read('README.rst'),
    author='Peter Bengtsson',
    author_email='mail@peterbe.com',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=find_install_requires(),
    entry_points={'console_scripts': ['mincss=mincss.main:main']},
    tests_require=['nose'],
    test_suite='tests.test_mincss',
    url='https://github.com/peterbe/mincss'
)
