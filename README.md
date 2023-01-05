# btclib_libsecp256k1

[![python](https://img.shields.io/pypi/pyversions/btclib_libsecp256k1.svg?logo=python)](https://pypi.python.org/pypi/btclib_libsecp256k1/)
[![pypi](https://img.shields.io/pypi/v/btclib_libsecp256k1.svg?logo=pypi)](https://pypi.python.org/pypi/btclib_libsecp256k1/)
[![downloads](https://static.pepy.tech/badge/btclib_libsecp256k1)](https://pepy.tech/project/btclib_libsecp256k1)
[![status](https://img.shields.io/pypi/status/btclib_libsecp256k1.svg)](https://pypi.python.org/pypi/btclib_libsecp256k1/)
[![license](https://img.shields.io/github/license/btclib-org/btclib_libsecp256k1.svg)](https://github.com/btclib-org/btclib_libsecp256k1/blob/master/LICENSE)
[![imports: isort](https://img.shields.io/badge/imports-isort-yellowgreen.svg?logo=isort)](https://pycqa.github.io/isort/)
[![code style: black](https://img.shields.io/badge/code%20style-black-yellowgreen.svg?logo=black)](https://github.com/psf/black)
[![lint: flake8](https://img.shields.io/badge/lint-flake8-yellowgreen.svg?logo=flake8)](https://flake8.pycqa.org)
[![lint: pylint](https://img.shields.io/badge/lint-pylint-yellowgreen.svg?logo=pylint)](https://github.com/PyCQA/pylint)
[![type-check: mypy](https://img.shields.io/badge/type--check-mypy-yellowgreen.svg?logo=mypy)](http://mypy-lang.org/)
[![type-check: pyright](https://img.shields.io/badge/type--check-pyright-yellowgreen.svg)](https://github.com/microsoft/pyright)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellowgreen.svg?logo=bandit)](https://github.com/PyCQA/bandit)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/btclib-org/btclib_libsecp256k1/master.svg)](https://results.pre-commit.ci/latest/github/btclib-org/btclib_libsecp256k1/master)
[![build](https://github.com/btclib-org/btclib_libsecp256k1/actions/workflows/build.yml/badge.svg)](https://github.com/btclib-org/btclib_libsecp256k1/actions/workflows/build.yml)
[![test](https://github.com/btclib-org/btclib_libsecp256k1/actions/workflows/test.yml/badge.svg)](https://github.com/btclib-org/btclib_libsecp256k1/actions/workflows/test.yml)

[![Follow on Twitter](https://img.shields.io/twitter/follow/btclib?style=social&logo=twitter)](https://twitter.com/intent/follow?screen_name=btclib)

---

[Browse GitHub Code Repository](https://github.com/btclib-org/btclib_libsecp256k1/)

---

Simple python bindings to
[libsecp256k1](https://github.com/bitcoin-core/secp256k1)
([v0.2.0](https://github.com/bitcoin-core/secp256k1/releases/tag/v0.2.0)).
It is intended to be used with the
[btclib](https://github.com/btclib-org/btclib) library.

To install (and/or upgrade):

    python -m pip install --upgrade btclib_libsecp256k1

## Build, test, develop, and contribute

Some development tools are required to develop and test btclib_libsecp256k1;
they can be installed with:

    python -m pip install --upgrade -r requirements-dev.txt

The btclib_libsecp256k1 project includes
[libsecp256k1](https://github.com/bitcoin-core/secp256k1)
as submodule in the secp256k1 folder.
By default, when cloning a project you get the directories that contain
submodules, but none of the files within them.
You must run `git submodule init` to initialize
your local configuration file,
and `git submodule update` to fetch the submodule data
and check out the appropriate commit.

<!-- markdownlint-disable MD013 -->
    $ git submodule init
    Submodule 'secp256k1' (git@github.com:bitcoin-core/secp256k1.git) registered for path 'secp256k1'
    $ git submodule update
    Cloning into 'secp256k1'...
<!-- markdownlint-enable MD013 -->

To build:

    python setup.py sdist
    python setup.py bdist_wheel --py-limited-api=cp36

Developers might also consider installing btclib_libsecp256k1 in editable way::

    python -m pip install --upgrade -e ./

To test:

    pytest

To measure the code coverage provided by tests:

    pytest --cov-report term-missing:skip-covered --cov=btclib_libsecp256k1

Pre-commit hooks are provided, please check before a PR

    pre-commit run --all-files
