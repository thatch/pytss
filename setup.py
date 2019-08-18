#!/usr/bin/env python3
"""
pytss is a python language wrapper for the Tspi library provided by the
TrouSerS project. libtspi is a library for interfacing with a TPM services
daemon.

Author: Matthew Garrett (matthew.garrett@nebula.com)

Copyright 2013 Nebula, Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from setuptools import setup, find_packages

__about__ = {}

with open('pytss/__about__.py') as fp:
    exec(fp.read(), None, __about__)


try:
    import pytss.interface
except ImportError:
    # installing - there is no cffi yet
    ext_modules = []
else:
    # building bdist - cffi is here!
    ext_modules = [pytss.interface.ffi.verifier.get_extension()]

setup(
    name=__about__['__title__'],
    version=__about__['__version__'],
    description=__about__['__summary__'],
    author=__about__['__author__'],
    author_email=__about__['__email__'],
    url='https://github.com/jmehta/python-tss/blob/master/setup.py',
    install_requires=['cffi', 'cryptography'],
    extras_require={
        'tests': ['pep8', 'pylint', 'pytest'],
    },
    tests_require=['pytest'],
    packages=find_packages(include=['pytss']),
    package_data={
        'pytss': ['interface.h'],
    },
    data_files = [('', ['LICENSE.txt'])],
    include_package_data=True,
    ext_modules=ext_modules,
    zip_safe=False,
)
