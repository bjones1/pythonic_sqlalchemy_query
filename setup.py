# .. License
#
#   Copyright 2017 Bryan A. Jones
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# *********************************************************
# |docname| - Package and install pythonic_sqlalchemy_query
# *********************************************************
# .. _to-package:
#
# To package
# ==========
# Create a source distribution, a built distribution, then upload both to
# `pythonic_sqlalchemy_query at PyPI <https://pypi.python.org/pypi/pythonic_sqlalchemy_query>`_::
#
#   python -m pip install -U pip setuptools wheel twine
#   python setup.py sdist bdist_wheel
#   python -m twine upload dist/*
#
# For `development
# <https://pythonhosted.org/setuptools/setuptools.html#development-mode>`_:
#
#  ``pip install -e .``
#
# Packaging script
# ================
# Otherwise known as the evils of ``setup.py``.
#
# PyPA copied code
# ----------------
# From `PyPA's sample setup.py
# <https://github.com/pypa/sampleproject/blob/master/setup.py>`__,
# read ``long_description`` from a file. This code was last updated on
# 26-May-2015 based on `this commit
# <https://github.com/pypa/sampleproject/commit/4687e26c8a61e72ae401ec94fc1e5c0e17465b73>`_.
#
# Always prefer setuptools over distutils
from setuptools import setup
# To use a consistent encoding
from os import path
# Imports for `version parse code`_.
import os
import re

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file.
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()
    # The inclusion of a raw tag causes `PyPI <http://pypi.python.org>`_ to not render the reST. Ouch. Remove it before uploading.
    long_description = re.sub('\.\. raw.*<\/iframe>', '', long_description, flags=re.DOTALL)

# This code was copied from `version parse code`_. See ``version`` in the call
# to ``setup`` below.
def read(*names, **kwargs):
    with open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

# My code
# -------
setup(
    # This must comply with `PEP 0426
    # <http://legacy.python.org/dev/peps/pep-0426/#name>`_'s
    # name requirements.
    name='pythonic_sqlalchemy_query',

    # Projects should comply with the `version scheme
    # <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
    # specified in PEP440. I use this so that my Sphinx docs will have the same
    # version number. There are a lot of alternatives in `Single-sourcing the
    # Project Version
    # <https://packaging.python.org/en/latest/single_source_version.html>`_.
    # While I like something simple, such as ``import pythonic_sqlalchemy_query`` then
    # ``version=pythonic_sqlalchemy_query.__version__`` here, this means any dependeninces of
    # `pythonic_sqlalchemy_query/__init__.py` will be requred to run setup,
    # a bad thing. So, instead I read the file in ``setup.py`` and parse the
    # version with a regex (see `version parse code
    # <https://packaging.python.org/en/latest/single_source_version.html#single-sourcing-the-project-version>`_).
    version=find_version("pythonic_sqlalchemy_query/__init__.py"),

    description="Provide concise, Pythonic query syntax for SQLAlchemy",
    long_description=long_description,

    # The project's main homepage.
    url='http://pythonic_sqlalchemy_query.readthedocs.io/en/latest/',

    author="Bryan A. Jones",
    author_email="bjones@ece.msstate.edu",

    license='GPLv3+',

    # These are taken from the `full list
    # <https://pypi.python.org/pypi?%3Aaction=list_classifiers>`_.
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Database',
    ],

    keywords='SQLAlchemy, query helper',

    packages=['pythonic_sqlalchemy_query'],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=([
        'SQLAlchemy',
    ]),

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    #
    #    ``$ pip install -e .[test]``
    extras_require={
        'test': ['pytest', 'Flask-SQLAlchemy'],
    },
)
