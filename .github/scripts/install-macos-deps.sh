#!/bin/bash

set -e
set -x

brew update

brew outdated openssl || brew upgrade openssl

# Install packages needed to build lib-secp256k1
for pkg in automake libtool pkg-config; do
    brew list $pkg > /dev/null || brew install $pkg
    brew outdated --quiet $pkg || brew upgrade $pkg
done

set +x +e
