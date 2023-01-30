# Copyright (C) The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

import sys

from setuptools import find_packages, setup  # type: ignore

sdist = "sdist" in sys.argv

setup(
    name="btclib_libsecp256k1",
    version="0.2.1",
    url="https://btclib.org",
    project_urls={
        "Download": "https://github.com/btclib-org/btclib_libsecp256k1/releases",
        # "Documentation": "https://btclib.readthedocs.io/",
        "GitHub": "https://github.com/btclib-org/btclib_libsecp256k1",
        "Issues": "https://github.com/btclib-org/btclib_libsecp256k1/issues",
        "Pull Requests": "https://github.com/btclib-org/btclib_libsecp256k1/pulls",
    },
    license="MIT",
    author="Giacomo Caironi",
    author_email="giacomo.caironi@gmail.com",
    description="Simple python bindings to libsecp256k1",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    package_data={"btclib_libsecp256k1": ["py.typed"]},
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=[] if sdist else ["build.py:ffi"],
    install_requires=["cffi>=1.0.0"],
    keywords=["bitcoin", "libsecp256k1"],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
