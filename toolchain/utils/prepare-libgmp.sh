#!/bin/bash
# Script to download and install libgmp if it is not already downloaded

# Copyright (C) 2020 Embecosm Limited

# Contributor: Simon Cook <simon.cook@embecosm.com>

# SPDX-License-Identifier: GPL-3.0-or-later

LIBGMP_VERS=6.2.1

(
  set -e
  set -x

  if which wget >/dev/null; then
    dl='wget'
  else
    dl='curl -LO'
  fi

  if [ ! -e gmp-${LIBGMP_VERS}/inst ]; then
    ${dl} https://gmplib.org/download/gmp/gmp-${LIBGMP_VERS}.tar.bz2
    tar -xjf gmp-${LIBGMP_VERS}.tar.bz2

    cd gmp-${LIBGMP_VERS}
    ./configure --enable-shared=no --enable-static=yes --prefix=$PWD/inst
    make
    make install
  fi
)
