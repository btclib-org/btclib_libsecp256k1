import sys

from setuptools import find_packages, setup

sdist = "sdist" in sys.argv

setup(
    name="btclib_libsecp256k1",
    version="0.0.1",
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
    description="Simple parser to libsecp256k1",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["build.py:ffi"] if not sdist else [],
    install_requires=["cffi>=1.0.0"],
    keywords=["bitcoin", "libsecp256k1"],
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
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
